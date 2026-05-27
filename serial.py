import time
from collections import defaultdict

CSV_FILE     = 'tabela.csv'
NUM_QUARTERS = 116          # Q1 1997 → Q4 2025
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

# ─── Utilitários ──────────────────────────────────────────────────────────────

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

# ─── Leitura ──────────────────────────────────────────────────────────────────

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

            # Strip aspas das colunas de metadado para comparações diretas
            row = linha.split(';')
            if len(row) < 3:
                continue
            row[0] = row[0].strip('"')   # nível:  BR / UF / MU
            row[1] = row[1].strip('"')   # local:  Brasil / São Paulo / ...
            row[2] = row[2].strip('"')   # inspeção: Total / Federal / ...

            if secao_atual == 'abatidos':
                rows_abatidos.append(row)
            else:
                rows_peso.append(row)

    return rows_abatidos, rows_peso

# ─── Filtros ──────────────────────────────────────────────────────────────────

def filtro_abate_por_estado(rows):
    """
    Filtro 1 — Total de cabeças abatidas por estado.
    Percorre TODAS as linhas calculando os totais mensais (pesado),
    depois agrega apenas as linhas de UF com inspeção Total.
    """
    result = defaultdict(float)
    for row in rows:
        anuais = calcular_por_ano(row)          # leitura mensal — executa para todas as linhas
        if row[0] == 'UF' and row[2] == 'Total':
            result[row[1]] += sum(anuais.values())
    return result

def filtro_evolucao_por_ano(rows):
    """
    Filtro 2 — Evolução anual de abates no Brasil.
    Agrega os dados mensais por ano para o nível BR / inspeção Total.
    """
    result = defaultdict(float)
    for row in rows:
        anuais = calcular_por_ano(row)
        if row[0] == 'BR' and row[2] == 'Total':
            for ano, v in anuais.items():
                result[ano] += v
    return result

def filtro_peso_por_regiao(rows):
    """
    Filtro 3 — Peso total das carcaças (kg) por região.
    Mesma lógica de cálculo mensal, agrega UF / inspeção Total por região.
    """
    result = defaultdict(float)
    for row in rows:
        anuais = calcular_por_ano(row)
        if row[0] == 'UF' and row[2] == 'Total':
            regiao = STATE_REGIONS.get(row[1])
            if regiao:
                result[regiao] += sum(anuais.values())
    return result

def filtro_inspecao(rows):
    """
    Filtro 4 — Comparação Federal × Estadual × Municipal no Brasil.
    """
    result = defaultdict(float)
    for row in rows:
        anuais = calcular_por_ano(row)
        if row[0] == 'BR' and row[2] in ('Federal', 'Estadual', 'Municipal'):
            result[row[2]] += sum(anuais.values())
    return result

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("   Análise Serial — Tabela 1092 IBGE")
    print("=" * 62)

    t0 = time.perf_counter()

    # ── Leitura ───────────────────────────────────────────────────────────────
    print("\n[1/5] Lendo arquivo...")
    print("      Percorrendo o CSV de 2 GB e carregando apenas as duas seções")
    print("      necessárias: 'Animais abatidos (Cabeças)' e")
    print("      'Peso total das carcaças (Quilogramas)'.")
    t_leit = time.perf_counter()
    rows_ab, rows_pe = ler_secoes()
    t_leit = time.perf_counter() - t_leit
    print(f"      -> {len(rows_ab):,} linhas carregadas para animais abatidos")
    print(f"      -> {len(rows_pe):,} linhas carregadas para peso das carcaças")
    print(f"      Tempo: {t_leit:.2f}s")

    # ── Filtro 1 ──────────────────────────────────────────────────────────────
    print("\n[2/5] Filtro 1 — Abate por Estado")
    print("      Percorre todas as linhas no nível UF com inspeção Total.")
    print("      Para cada estado, soma os abates mês a mês (3 meses × 4")
    print("      trimestres × 29 anos = 348 leituras por linha) de 1997 a 2025.")
    t = time.perf_counter()
    r1 = filtro_abate_por_estado(rows_ab)
    t1 = time.perf_counter() - t
    print(f"\n      -> {len(r1)} estados encontrados. Ranking por volume de abate:\n")
    print(f"      {'Estado':<25} {'Total de Cabeças':>20}  Rank")
    print(f"      {'-'*25} {'-'*20}  ----")
    for rank, (est, v) in enumerate(sorted(r1.items(), key=lambda x: -x[1]), 1):
        print(f"      {est:<25} {v:>20,.0f}  #{rank}")
    print(f"\n      Tempo: {t1:.2f}s")

    # ── Filtro 2 ──────────────────────────────────────────────────────────────
    print("\n[3/5] Filtro 2 — Evolução Anual (Brasil)")
    print("      Agrupa os abates mensais por ano para o nível Brasil,")
    print("      inspeção Total. Calcula também a variação em relação ao")
    print("      ano anterior para revelar tendências de crescimento ou queda.")
    t = time.perf_counter()
    r2 = filtro_evolucao_por_ano(rows_ab)
    t2 = time.perf_counter() - t
    anos = sorted(r2)
    print(f"\n      -> {len(anos)} anos analisados ({anos[0]}–{anos[-1]}):\n")
    print(f"      {'Ano':>6}  {'Total de Cabeças':>20}  {'Var. s/ ano ant.':>16}")
    print(f"      {'------':>6}  {'-'*20}  {'-'*16}")
    for i, ano in enumerate(anos):
        v = r2[ano]
        var = "    —" if i == 0 else f"{'+'if v-r2[anos[i-1]]>=0 else ''}{v-r2[anos[i-1]]:,.0f}"
        print(f"      {ano:>6}  {v:>20,.0f}  {var:>16}")
    print(f"\n      Tempo: {t2:.2f}s")

    # ── Filtro 3 ──────────────────────────────────────────────────────────────
    print("\n[4/5] Filtro 3 — Peso Total das Carcaças por Região (kg)")
    print("      Usa a seção de peso das carcaças. Para cada estado (UF),")
    print("      inspeção Total, soma o peso em kg mês a mês e agrupa")
    print("      pelos 5 grupos regionais do Brasil.")
    t = time.perf_counter()
    r3 = filtro_peso_por_regiao(rows_pe)
    t3 = time.perf_counter() - t
    tg = sum(r3.values())
    print(f"\n      -> {len(r3)} regiões | peso total acumulado: {tg:,.0f} kg\n")
    print(f"      {'Região':<15} {'Peso Total (kg)':>22}  {'% do Brasil':>12}")
    print(f"      {'-'*15} {'-'*22}  {'-'*12}")
    for reg, v in sorted(r3.items(), key=lambda x: -x[1]):
        print(f"      {reg:<15} {v:>22,.0f}  {(v/tg*100) if tg else 0:>11.1f}%")
    print(f"\n      Tempo: {t3:.2f}s")

    # ── Filtro 4 ──────────────────────────────────────────────────────────────
    print("\n[5/5] Filtro 4 — Federal × Estadual × Municipal (Brasil)")
    print("      Filtra as linhas do nível Brasil separadas por tipo de")
    print("      inspeção sanitária (Federal, Estadual, Municipal).")
    print("      Mostra qual esfera fiscalizou mais cabeças no período total.")
    t = time.perf_counter()
    r4 = filtro_inspecao(rows_ab)
    t4 = time.perf_counter() - t
    ti = sum(r4.values())
    print(f"\n      -> total fiscalizado no período: {ti:,.0f} cabeças\n")
    print(f"      {'Inspeção':<12} {'Total de Cabeças':>22}  {'% do Total':>10}")
    print(f"      {'-'*12} {'-'*22}  {'-'*10}")
    for tipo, v in sorted(r4.items(), key=lambda x: -x[1]):
        print(f"      {tipo:<12} {v:>22,.0f}  {(v/ti*100) if ti else 0:>9.1f}%")
    print(f"\n      Tempo: {t4:.2f}s")

    # ── Resumo ────────────────────────────────────────────────────────────────
    total = time.perf_counter() - t0
    print("\n" + "=" * 62)
    print("   Resumo de Tempos")
    print("=" * 62)
    print(f"   Leitura do arquivo : {t_leit:>8.2f}s")
    print(f"   Filtro 1           : {t1:>8.2f}s")
    print(f"   Filtro 2           : {t2:>8.2f}s")
    print(f"   Filtro 3           : {t3:>8.2f}s")
    print(f"   Filtro 4           : {t4:>8.2f}s")
    print(f"   TOTAL              : {total:>8.2f}s")
    print("=" * 62)

if __name__ == '__main__':
    main()
