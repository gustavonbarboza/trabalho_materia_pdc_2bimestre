"""
paralelizado.py
Roda os mesmos 4 filtros do serial.py, mas divide as linhas
entre N threads. Cada rodada (2, 4, 6, 8, 12 threads) exibe
os resultados completos + tempo, igual ao serial — só mais rápido.
"""
import time
import threading
from collections import defaultdict

CSV_FILE      = 'tabela1092_2GB.csv'
THREAD_COUNTS = [2, 4, 6, 8, 12]

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

# ─── Utilitários ──────────────────────────────────────────────────────────────

def parse_val(s):
    s = s.strip().strip('"')
    if s in ('-', '...', '', 'X'):
        return 0.0
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except ValueError:
        return 0.0

def quarter_col(q):
    return 3 + q * 24

# ─── Leitura (igual ao serial) ────────────────────────────────────────────────

def ler_secoes():
    rows_abatidos = []
    rows_peso     = []
    secao_atual   = None
    cabecalhos    = 0

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
            if secao_atual == 'abatidos':
                rows_abatidos.append(row)
            else:
                rows_peso.append(row)

    return rows_abatidos, rows_peso

# ─── Worker: cada thread roda os 4 filtros na sua fatia ───────────────────────

def worker(rows_ab, rows_pe, resultados, idx):
    """
    Cada thread recebe sua fatia de linhas e computa
    resultados parciais dos 4 filtros de forma independente.
    Sem Lock necessário — cada thread escreve no seu próprio índice.
    """
    r1 = defaultdict(float)   # filtro 1 — abate por estado
    r2 = defaultdict(float)   # filtro 2 — evolução por ano
    r3 = defaultdict(float)   # filtro 3 — peso por região
    r4 = defaultdict(float)   # filtro 4 — tipo de inspeção

    for row in rows_ab:
        nivel = row[0].strip('"')
        estado = row[1].strip('"')
        insp  = row[2].strip('"')

        # Filtro 1 — abate por estado (UF, inspeção Total)
        if nivel == 'UF' and insp == 'Total':
            total = sum(parse_val(row[quarter_col(q)])
                        for q in range(NUM_QUARTERS) if quarter_col(q) < len(row))
            r1[estado] += total

        # Filtro 2 — evolução anual (Brasil, inspeção Total)
        if nivel == 'BR' and insp == 'Total':
            for y in range(NUM_YEARS):
                ano = START_YEAR + y
                for q in range(4):
                    col = quarter_col(y * 4 + q)
                    if col < len(row):
                        r2[ano] += parse_val(row[col])

        # Filtro 4 — Federal × Estadual × Municipal (Brasil)
        if nivel == 'BR' and insp in ('Federal', 'Estadual', 'Municipal'):
            total = sum(parse_val(row[quarter_col(q)])
                        for q in range(NUM_QUARTERS) if quarter_col(q) < len(row))
            r4[insp] += total

    for row in rows_pe:
        nivel = row[0].strip('"')
        estado = row[1].strip('"')
        insp  = row[2].strip('"')

        # Filtro 3 — peso por região (UF, inspeção Total)
        if nivel == 'UF' and insp == 'Total':
            regiao = STATE_REGIONS.get(estado)
            if regiao:
                total = sum(parse_val(row[quarter_col(q)])
                            for q in range(NUM_QUARTERS) if quarter_col(q) < len(row))
                r3[regiao] += total

    resultados[idx] = (r1, r2, r3, r4)

# ─── Divisão e merge ──────────────────────────────────────────────────────────

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
    for parcial in resultados:
        p1, p2, p3, p4 = parcial
        for k, v in p1.items(): r1[k] += v
        for k, v in p2.items(): r2[k] += v
        for k, v in p3.items(): r3[k] += v
        for k, v in p4.items(): r4[k] += v

    return r1, r2, r3, r4

# ─── Exibição (igual ao serial) ───────────────────────────────────────────────

def exibir_resultados(r1, r2, r3, r4):
    # Filtro 1
    print("\n  Filtro 1 — Abate por Estado")
    print(f"  {'Estado':<25} {'Total de Cabeças':>20}  Rank")
    print(f"  {'-'*25} {'-'*20}  ----")
    for rank, (est, v) in enumerate(sorted(r1.items(), key=lambda x: -x[1]), 1):
        print(f"  {est:<25} {v:>20,.0f}  #{rank}")

    # Filtro 2
    print("\n  Filtro 2 — Evolução Anual (Brasil)")
    print(f"  {'Ano':>6}  {'Total de Cabeças':>20}  {'Var. s/ ano ant.':>16}")
    print(f"  {'------':>6}  {'-'*20}  {'-'*16}")
    anos = sorted(r2)
    for i, ano in enumerate(anos):
        v = r2[ano]
        var = "    —" if i == 0 else f"{'+'if r2[ano]-r2[anos[i-1]]>=0 else ''}{r2[ano]-r2[anos[i-1]]:,.0f}"
        print(f"  {ano:>6}  {v:>20,.0f}  {var:>16}")

    # Filtro 3
    print("\n  Filtro 3 — Peso Total por Região (kg)")
    total_geral = sum(r3.values())
    print(f"  {'Região':<15} {'Peso Total (kg)':>22}  {'% do Brasil':>12}")
    print(f"  {'-'*15} {'-'*22}  {'-'*12}")
    for reg, v in sorted(r3.items(), key=lambda x: -x[1]):
        pct = (v / total_geral * 100) if total_geral else 0
        print(f"  {reg:<15} {v:>22,.0f}  {pct:>11.1f}%")

    # Filtro 4
    print("\n  Filtro 4 — Federal × Estadual × Municipal (Brasil)")
    total_insp = sum(r4.values())
    print(f"  {'Inspeção':<12} {'Total de Cabeças':>22}  {'% do Total':>10}")
    print(f"  {'-'*12} {'-'*22}  {'-'*10}")
    for tipo, v in sorted(r4.items(), key=lambda x: -x[1]):
        pct = (v / total_insp * 100) if total_insp else 0
        print(f"  {tipo:<12} {v:>22,.0f}  {pct:>9.1f}%")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("   Análise Paralela (Threads) — Tabela 1092 IBGE")
    print("=" * 62)

    print("\nLendo arquivo...")
    t_leit = time.perf_counter()
    rows_ab, rows_pe = ler_secoes()
    t_leit = time.perf_counter() - t_leit
    print(f"  {len(rows_ab):,} linhas (abatidos) | {len(rows_pe):,} linhas (peso)")
    print(f"  Tempo de leitura: {t_leit:.2f}s")

    tempos = {}

    for n in THREAD_COUNTS:
        print(f"\n{'=' * 62}")
        print(f"   Rodada com {n} threads")
        print(f"{'=' * 62}")

        t0 = time.perf_counter()
        r1, r2, r3, r4 = rodar_com_n_threads(rows_ab, rows_pe, n)
        elapsed = time.perf_counter() - t0
        tempos[n] = elapsed

        exibir_resultados(r1, r2, r3, r4)
        print(f"\n  Tempo de processamento ({n} threads): {elapsed:.4f}s")

    # ── Tabela de speedup ─────────────────────────────────────────
    print(f"\n{'=' * 62}")
    print("   Tabela de Speedup")
    print(f"{'=' * 62}")
    t_ref = tempos[THREAD_COUNTS[0]]   # referência = 2 threads
    print(f"  {'Threads':>8}  {'Tempo (s)':>12}  {'Speedup':>10}")
    print(f"  {'-'*8}  {'-'*12}  {'-'*10}")
    for n in THREAD_COUNTS:
        sp = t_ref / tempos[n]
        print(f"  {n:>8}  {tempos[n]:>12.4f}  {sp:>9.2f}x")
    print("=" * 62)

if __name__ == '__main__':
    main()
