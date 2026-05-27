"""
paralelizado.py — mesmos 4 filtros do serial.py, mas com N threads.
Rodado para N = 2, 4, 6, 8, 12; exibe tabela de speedup ao final.
"""
import time
import threading
from collections import defaultdict

CSV_FILE = 'tabela1092_2GB.csv'
THREAD_COUNTS = [2, 4, 6, 8, 12]

NUM_QUARTERS = 116
START_YEAR   = 1997
NUM_YEARS    = 29

STATE_REGIONS = {
    'Rondônia': 'Norte',      'Acre': 'Norte',           'Amazonas': 'Norte',
    'Roraima': 'Norte',       'Pará': 'Norte',            'Amapá': 'Norte',
    'Tocantins': 'Norte',
    'Maranhão': 'Nordeste',   'Piauí': 'Nordeste',        'Ceará': 'Nordeste',
    'Rio Grande do Norte': 'Nordeste', 'Paraíba': 'Nordeste', 'Pernambuco': 'Nordeste',
    'Alagoas': 'Nordeste',    'Sergipe': 'Nordeste',      'Bahia': 'Nordeste',
    'Minas Gerais': 'Sudeste','Espírito Santo': 'Sudeste','Rio de Janeiro': 'Sudeste',
    'São Paulo': 'Sudeste',
    'Paraná': 'Sul',          'Santa Catarina': 'Sul',    'Rio Grande do Sul': 'Sul',
    'Mato Grosso do Sul': 'Centro-Oeste', 'Mato Grosso': 'Centro-Oeste',
    'Goiás': 'Centro-Oeste',  'Distrito Federal': 'Centro-Oeste',
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

# ─── Leitura (idêntica ao serial) ─────────────────────────────────────────────

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

# ─── Workers (um por filtro, recebe fatia de linhas) ─────────────────────────

def worker_abate_estado(rows, resultado, lock):
    parcial = defaultdict(float)
    for row in rows:
        if row[0] == 'UF' and row[2] == 'Total':
            total = sum(parse_val(row[quarter_col(q)])
                        for q in range(NUM_QUARTERS) if quarter_col(q) < len(row))
            parcial[row[1]] += total
    with lock:
        for k, v in parcial.items():
            resultado[k] += v

def worker_evolucao(rows, resultado, lock):
    parcial = defaultdict(float)
    for row in rows:
        if row[0] == 'BR' and row[2] == 'Total':
            for y in range(NUM_YEARS):
                for q in range(4):
                    col = quarter_col(y * 4 + q)
                    if col < len(row):
                        parcial[START_YEAR + y] += parse_val(row[col])
    with lock:
        for k, v in parcial.items():
            resultado[k] += v

def worker_peso_regiao(rows, resultado, lock):
    parcial = defaultdict(float)
    for row in rows:
        if row[0] == 'UF' and row[2] == 'Total':
            regiao = STATE_REGIONS.get(row[1])
            if regiao:
                total = sum(parse_val(row[quarter_col(q)])
                            for q in range(NUM_QUARTERS) if quarter_col(q) < len(row))
                parcial[regiao] += total
    with lock:
        for k, v in parcial.items():
            resultado[k] += v

def worker_inspecao(rows, resultado, lock):
    parcial = defaultdict(float)
    for row in rows:
        if row[0] == 'BR' and row[2] in ('Federal', 'Estadual', 'Municipal'):
            total = sum(parse_val(row[quarter_col(q)])
                        for q in range(NUM_QUARTERS) if quarter_col(q) < len(row))
            parcial[row[2]] += total
    with lock:
        for k, v in parcial.items():
            resultado[k] += v

# ─── Executor paralelo ────────────────────────────────────────────────────────

def dividir(lst, n):
    """Divide lista em n fatias aproximadamente iguais."""
    tam = len(lst)
    inicio = 0
    for i in range(n):
        fim = inicio + (tam - inicio) // (n - i)
        yield lst[inicio:fim]
        inicio = fim

def rodar_paralelo(rows_ab, rows_pe, n_threads):
    lock_1 = threading.Lock()
    lock_2 = threading.Lock()
    lock_3 = threading.Lock()
    lock_4 = threading.Lock()

    res1 = defaultdict(float)
    res2 = defaultdict(float)
    res3 = defaultdict(float)
    res4 = defaultdict(float)

    threads = []

    fatias_ab = list(dividir(rows_ab, n_threads))
    fatias_pe = list(dividir(rows_pe, n_threads))

    for i in range(n_threads):
        threads.append(threading.Thread(target=worker_abate_estado,
                                        args=(fatias_ab[i], res1, lock_1)))
        threads.append(threading.Thread(target=worker_evolucao,
                                        args=(fatias_ab[i], res2, lock_2)))
        threads.append(threading.Thread(target=worker_peso_regiao,
                                        args=(fatias_pe[i], res3, lock_3)))
        threads.append(threading.Thread(target=worker_inspecao,
                                        args=(fatias_ab[i], res4, lock_4)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return res1, res2, res3, res4

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("   Análise Paralela (Threads) — Tabela 1092 IBGE")
    print("=" * 65)

    print("\nLendo arquivo (leitura serial única)...")
    t_leit = time.perf_counter()
    rows_ab, rows_pe = ler_secoes()
    t_leit = time.perf_counter() - t_leit
    print(f"  {len(rows_ab):,} linhas (abatidos) | {len(rows_pe):,} linhas (peso)")
    print(f"  Tempo de leitura: {t_leit:.2f}s\n")

    tempos = {}

    for n in THREAD_COUNTS:
        print(f"── {n} threads ──────────────────────────────────────────")
        t0 = time.perf_counter()
        res1, res2, res3, res4 = rodar_paralelo(rows_ab, rows_pe, n)
        elapsed = time.perf_counter() - t0
        tempos[n] = elapsed
        print(f"   Tempo de processamento: {elapsed:.4f}s")

    # Referência: 1 thread (serial dos filtros, sem I/O)
    print("\n── 1 thread (referência) ────────────────────────────────")
    t0 = time.perf_counter()
    rodar_paralelo(rows_ab, rows_pe, 1)
    t_serial = time.perf_counter() - t0
    print(f"   Tempo de processamento: {t_serial:.4f}s")

    # ── Tabela de speedup ──
    print("\n" + "=" * 65)
    print(f"   {'Threads':>8}  {'Tempo (s)':>12}  {'Speedup':>10}")
    print("   " + "-" * 36)
    print(f"   {'1':>8}  {t_serial:>12.4f}  {'1.00x':>10}")
    for n in THREAD_COUNTS:
        sp = t_serial / tempos[n]
        print(f"   {n:>8}  {tempos[n]:>12.4f}  {sp:>9.2f}x")
    print("=" * 65)

    # ── Exibe resultados do último run (12 threads) ──
    res1, res2, res3, res4 = rodar_paralelo(rows_ab, rows_pe, 12)

    print("\nFiltro 1 — Top 10 estados por abate:")
    for est, v in sorted(res1.items(), key=lambda x: -x[1])[:10]:
        print(f"  {est:<25} {v:>18,.0f}")

    print("\nFiltro 2 — Evolução anual (Brasil):")
    for ano in sorted(res2):
        print(f"  {ano}: {res2[ano]:>18,.0f}")

    print("\nFiltro 3 — Peso por região (kg):")
    for reg, v in sorted(res3.items(), key=lambda x: -x[1]):
        print(f"  {reg:<15} {v:>22,.0f}")

    print("\nFiltro 4 — Federal × Estadual × Municipal:")
    for tipo, v in sorted(res4.items(), key=lambda x: -x[1]):
        print(f"  {tipo:<10} {v:>22,.0f}")

if __name__ == '__main__':
    main()
