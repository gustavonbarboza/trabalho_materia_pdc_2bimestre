"""
paralelizado.py
Roda os mesmos 4 filtros do serial.py dividindo as linhas entre N threads.
Para N = 2, 4, 6, 8, 12: exibe o cabeçalho da rodada, os resultados
completos dos filtros e o tempo — igual ao serial, só mais rápido.
"""
import time
import threading
from collections import defaultdict

CSV_FILE      = 'tabela.csv'
THREAD_COUNTS = [2, 4, 8, 12]

NUM_QUARTERS = 116
START_YEAR   = 1997
NUM_YEARS    = 29

STATE_REGIONS = {
    'Rondônia': 'Norte',       'Acre': 'Norte',            'Amazonas': 'Norte',
    'Roraima': 'Norte',        'Pará': 'Norte',             'Amapá': 'Norte',
    'Tocantins': 'Norte',
    'Maranhão': 'Nordeste',    'Piauí': 'Nordeste',         'Ceará': 'Nordeste',
    'Rio Grande do Norte': 'Nordeste', 'Paraíba': 'Nordeste', 'Pernambuco': 'Nordeste',
    'Alagoas': 'Nordeste',     'Sergipe': 'Nordeste',       'Bahia': 'Nordeste',
    'Minas Gerais': 'Sudeste', 'Espírito Santo': 'Sudeste', 'Rio de Janeiro': 'Sudeste',
    'São Paulo': 'Sudeste',
    'Paraná': 'Sul',           'Santa Catarina': 'Sul',     'Rio Grande do Sul': 'Sul',
    'Mato Grosso do Sul': 'Centro-Oeste', 'Mato Grosso': 'Centro-Oeste',
    'Goiás': 'Centro-Oeste',   'Distrito Federal': 'Centro-Oeste',
}

# ─── Utilitários (idênticos ao serial) ───────────────────────────────────────

def parse_val(s):
    s = s.strip().strip('"')
    if s in ('-', '...', '', 'X'):
        return 0.0
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except ValueError:
        return 0.0

def calcular_por_ano(row):
    """
    Soma os animais por ano usando os dados de CADA MÊS individualmente
    (3 meses × 4 trimestres × 29 anos = 348 leituras por linha).
    Coluna do mês M no trimestre Q:  3 + Q*24 + M*6   (M = 1, 2, 3)
    """
    anuais = defaultdict(float)
    for y in range(NUM_YEARS):
        ano = START_YEAR + y
        for q in range(4):
            qi = y * 4 + q
            for m in range(1, 4):
                col = 3 + qi * 24 + m * 6
                if col < len(row):
                    anuais[ano] += parse_val(row[col])
    return anuais

# ─── Leitura (idêntica ao serial) ────────────────────────────────────────────

def ler_secoes():
    rows_abatidos, rows_peso = [], []
    secao_atual, cabecalhos  = None, 0

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        for linha in f:
            linha = linha.rstrip('\n')
            if not linha:
                continue
            primeiro = linha.split(';')[0].strip('"')
            if primeiro.startswith('Variável'):
                if 'Animais abatidos (Cabeças)' in linha:
                    secao_atual = 'abatidos'
                elif 'Peso total das carcaças (Quilogramas)' in linha:
                    secao_atual = 'peso'
                else:
                    secao_atual = None
                cabecalhos = 0
                continue
            if secao_atual is None:
                continue
            if cabecalhos < 4:
                cabecalhos += 1
                continue
            row = linha.split(';')
            if len(row) < 3:
                continue
            row[0] = row[0].strip('"')
            row[1] = row[1].strip('"')
            row[2] = row[2].strip('"')
            if secao_atual == 'abatidos':
                rows_abatidos.append(row)
            else:
                rows_peso.append(row)

    return rows_abatidos, rows_peso

# ─── Worker: cada thread roda os 4 filtros na sua fatia ──────────────────────

def worker(rows_ab, rows_pe, resultados, idx):
    """
    Recebe uma fatia de linhas e computa os 4 filtros de forma independente.
    Cada thread escreve apenas no seu índice → sem Lock, sem condição de corrida.
    """
    r1 = defaultdict(float)
    r2 = defaultdict(float)
    r3 = defaultdict(float)
    r4 = defaultdict(float)

    for row in rows_ab:
        anuais = calcular_por_ano(row)

        if row[0] == 'UF' and row[2] == 'Total':
            r1[row[1]] += sum(anuais.values())

        if row[0] == 'BR' and row[2] == 'Total':
            for ano, v in anuais.items():
                r2[ano] += v

        if row[0] == 'BR' and row[2] in ('Federal', 'Estadual', 'Municipal'):
            r4[row[2]] += sum(anuais.values())

    for row in rows_pe:
        anuais = calcular_por_ano(row)
        if row[0] == 'UF' and row[2] == 'Total':
            regiao = STATE_REGIONS.get(row[1])
            if regiao:
                r3[regiao] += sum(anuais.values())

    resultados[idx] = (r1, r2, r3, r4)

# ─── Divisão e merge ─────────────────────────────────────────────────────────

def dividir(lst, n):
    tam, inicio = len(lst), 0
    for i in range(n):
        fim = inicio + (tam - inicio) // (n - i)
        yield lst[inicio:fim]
        inicio = fim

def rodar_com_n_threads(rows_ab, rows_pe, n):
    fatias_ab  = list(dividir(rows_ab, n))
    fatias_pe  = list(dividir(rows_pe, n))
    resultados = [None] * n

    threads = [
        threading.Thread(target=worker, args=(fatias_ab[i], fatias_pe[i], resultados, i))
        for i in range(n)
    ]
    for t in threads: t.start()
    for t in threads: t.join()

    # Merge: soma os dicionários parciais de cada thread
    r1, r2, r3, r4 = (defaultdict(float) for _ in range(4))
    for p1, p2, p3, p4 in resultados:
        for k, v in p1.items(): r1[k] += v
        for k, v in p2.items(): r2[k] += v
        for k, v in p3.items(): r3[k] += v
        for k, v in p4.items(): r4[k] += v

    return r1, r2, r3, r4

# ─── Exibição dos filtros (idêntica ao serial) ────────────────────────────────

def exibir_filtros(r1, r2, r3, r4, n_threads):
    # Filtro 1
    print("\n[2/5] Filtro 1 — Abate por Estado")
    print("      Percorre todas as linhas no nível UF com inspeção Total.")
    print("      Para cada estado, soma os abates mês a mês (3 meses × 4")
    print("      trimestres × 29 anos = 348 leituras por linha) de 1997 a 2025.")
    print(f"\n      -> {len(r1)} estados encontrados. Ranking por volume de abate:\n")
    print(f"      {'Estado':<25} {'Total de Cabeças':>20}  Rank")
    print(f"      {'-'*25} {'-'*20}  ----")
    for rank, (est, v) in enumerate(sorted(r1.items(), key=lambda x: -x[1]), 1):
        print(f"      {est:<25} {v:>20,.0f}  #{rank}")

    # Filtro 2
    print("\n[3/5] Filtro 2 — Evolução Anual (Brasil)")
    print("      Agrupa os abates mensais por ano para o nível Brasil,")
    print("      inspeção Total. Calcula também a variação em relação ao")
    print("      ano anterior para revelar tendências de crescimento ou queda.")
    anos = sorted(r2)
    print(f"\n      -> {len(anos)} anos analisados ({anos[0]}–{anos[-1]}):\n")
    print(f"      {'Ano':>6}  {'Total de Cabeças':>20}  {'Var. s/ ano ant.':>16}")
    print(f"      {'------':>6}  {'-'*20}  {'-'*16}")
    for i, ano in enumerate(anos):
        v = r2[ano]
        var = "    —" if i == 0 else f"{'+'if v-r2[anos[i-1]]>=0 else ''}{v-r2[anos[i-1]]:,.0f}"
        print(f"      {ano:>6}  {v:>20,.0f}  {var:>16}")

    # Filtro 3
    print("\n[4/5] Filtro 3 — Peso Total das Carcaças por Região (kg)")
    print("      Usa a seção de peso das carcaças. Para cada estado (UF),")
    print("      inspeção Total, soma o peso em kg mês a mês e agrupa")
    print("      pelos 5 grupos regionais do Brasil.")
    tg = sum(r3.values())
    print(f"\n      -> {len(r3)} regiões | peso total acumulado: {tg:,.0f} kg\n")
    print(f"      {'Região':<15} {'Peso Total (kg)':>22}  {'% do Brasil':>12}")
    print(f"      {'-'*15} {'-'*22}  {'-'*12}")
    for reg, v in sorted(r3.items(), key=lambda x: -x[1]):
        print(f"      {reg:<15} {v:>22,.0f}  {(v/tg*100) if tg else 0:>11.1f}%")

    # Filtro 4
    print("\n[5/5] Filtro 4 — Federal × Estadual × Municipal (Brasil)")
    print("      Filtra as linhas do nível Brasil separadas por tipo de")
    print("      inspeção sanitária (Federal, Estadual, Municipal).")
    print("      Mostra qual esfera fiscalizou mais cabeças no período total.")
    ti = sum(r4.values())
    print(f"\n      -> total fiscalizado no período: {ti:,.0f} cabeças\n")
    print(f"      {'Inspeção':<12} {'Total de Cabeças':>22}  {'% do Total':>10}")
    print(f"      {'-'*12} {'-'*22}  {'-'*10}")
    for tipo, v in sorted(r4.items(), key=lambda x: -x[1]):
        print(f"      {tipo:<12} {v:>22,.0f}  {(v/ti*100) if ti else 0:>9.1f}%")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("   Análise Paralela (Threads) — Tabela 1092 IBGE")
    print("=" * 62)

    # Leitura feita uma única vez, antes de todas as rodadas
    print("\n[1/5] Lendo arquivo...")
    print("      Percorrendo o CSV de 8 GB e carregando apenas as duas seções")
    print("      necessárias: 'Animais abatidos (Cabeças)' e")
    print("      'Peso total das carcaças (Quilogramas)'.")
    t_leit = time.perf_counter()
    rows_ab, rows_pe = ler_secoes()
    t_leit = time.perf_counter() - t_leit
    print(f"      -> {len(rows_ab):,} linhas carregadas para animais abatidos")
    print(f"      -> {len(rows_pe):,} linhas carregadas para peso das carcaças")
    print(f"      Tempo de leitura: {t_leit:.2f}s")

    tempos = {}

    for n in THREAD_COUNTS:
        print(f"\n\n{'=' * 62}")
        print(f"{'':^10}{'=' * 10}  {n} THREADS  {'=' * 10}")
        print(f"{'=' * 62}")

        t0 = time.perf_counter()
        r1, r2, r3, r4 = rodar_com_n_threads(rows_ab, rows_pe, n)
        t_proc = time.perf_counter() - t0

        tempos[n] = t_proc

        exibir_filtros(r1, r2, r3, r4, n)

        print(f"\n{'=' * 62}")
        print(f"   Resumo — {n} threads")
        print(f"{'=' * 62}")
        print(f"   Leitura (compartilhada) : {t_leit:>8.2f}s")
        print(f"   Processamento paralelo  : {t_proc:>8.2f}s")
        print(f"   TOTAL                   : {t_leit + t_proc:>8.2f}s")
        print(f"{'=' * 62}")

    # ── Tabela de speedup ─────────────────────────────────────────────────────
    t_ref = tempos[THREAD_COUNTS[0]]
    print(f"\n\n{'=' * 62}")
    print("   Comparativo de Speedup (processamento)")
    print(f"{'=' * 62}")
    print(f"   {'Threads':>8}  {'Tempo proc. (s)':>16}  {'Speedup':>10}")
    print(f"   {'-'*8}  {'-'*16}  {'-'*10}")
    for n in THREAD_COUNTS:
        sp = t_ref / tempos[n]
        print(f"   {n:>8}  {tempos[n]:>16.2f}  {sp:>9.2f}x")
    print("=" * 62)

if __name__ == '__main__':
    main()
