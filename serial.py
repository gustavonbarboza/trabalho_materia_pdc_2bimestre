import time
from collections import defaultdict

CSV_FILE = 'tabela1092_2GB.csv'

# 116 trimestres: Q1 1997 a Q4 2025  (29 anos × 4)
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

def parse_val(s):
    s = s.strip().strip('"')
    if s in ('-', '...', '', 'X'):
        return 0.0
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except ValueError:
        return 0.0

def quarter_col(q):
    """Índice da coluna 'Total do trimestre / Total' para o trimestre q (0-based)."""
    return 3 + q * 24

# ─── Filtros ──────────────────────────────────────────────────────────────────

def filtro_abate_por_estado(rows):
    """Total acumulado de cabeças abatidas por estado (UF, inspeção Total)."""
    result = defaultdict(float)
    for row in rows:
        if row[0] == 'UF' and row[2] == 'Total':
            total = sum(parse_val(row[quarter_col(q)])
                        for q in range(NUM_QUARTERS) if quarter_col(q) < len(row))
            result[row[1]] += total
    return result

def filtro_evolucao_por_ano(rows):
    """Evolução anual de cabeças abatidas no Brasil."""
    result = defaultdict(float)
    for row in rows:
        if row[0] == 'BR' and row[2] == 'Total':
            for y in range(NUM_YEARS):
                year = START_YEAR + y
                for q in range(4):
                    col = quarter_col(y * 4 + q)
                    if col < len(row):
                        result[year] += parse_val(row[col])
    return result

def filtro_peso_por_regiao(rows):
    """Peso total das carcaças (kg) agrupado por região geográfica."""
    result = defaultdict(float)
    for row in rows:
        if row[0] == 'UF' and row[2] == 'Total':
            regiao = STATE_REGIONS.get(row[1])
            if regiao:
                total = sum(parse_val(row[quarter_col(q)])
                            for q in range(NUM_QUARTERS) if quarter_col(q) < len(row))
                result[regiao] += total
    return result

def filtro_inspecao(rows):
    """Comparação Federal × Estadual × Municipal (nível Brasil)."""
    result = defaultdict(float)
    for row in rows:
        if row[0] == 'BR' and row[2] in ('Federal', 'Estadual', 'Municipal'):
            total = sum(parse_val(row[quarter_col(q)])
                        for q in range(NUM_QUARTERS) if quarter_col(q) < len(row))
            result[row[2]] += total
    return result

# ─── Leitura ──────────────────────────────────────────────────────────────────

def ler_secoes():
    """Lê apenas as duas seções necessárias: Animais abatidos e Peso total."""
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

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("   Análise Serial — Tabela 1092 IBGE")
    print("=" * 60)

    t0 = time.perf_counter()

    print("\n[1/5] Lendo arquivo...")
    t_leitura = time.perf_counter()
    rows_ab, rows_pe = ler_secoes()
    t_leitura = time.perf_counter() - t_leitura
    print(f"      {len(rows_ab):,} linhas (abatidos) | {len(rows_pe):,} linhas (peso)")
    print(f"      Tempo de leitura: {t_leitura:.2f}s")

    # ── Filtro 1 ──
    print("\n[2/5] Filtro 1 — Abate por Estado")
    t = time.perf_counter()
    abate_estado = filtro_abate_por_estado(rows_ab)
    t1 = time.perf_counter() - t
    top10 = sorted(abate_estado.items(), key=lambda x: -x[1])[:10]
    for estado, v in top10:
        print(f"      {estado:<25} {v:>18,.0f} cabeças")
    print(f"      Tempo: {t1:.4f}s")

    # ── Filtro 2 ──
    print("\n[3/5] Filtro 2 — Evolução Anual (Brasil)")
    t = time.perf_counter()
    evolucao = filtro_evolucao_por_ano(rows_ab)
    t2 = time.perf_counter() - t
    for ano in sorted(evolucao):
        print(f"      {ano}: {evolucao[ano]:>18,.0f} cabeças")
    print(f"      Tempo: {t2:.4f}s")

    # ── Filtro 3 ──
    print("\n[4/5] Filtro 3 — Peso Total por Região (kg)")
    t = time.perf_counter()
    peso_regiao = filtro_peso_por_regiao(rows_pe)
    t3 = time.perf_counter() - t
    for reg, v in sorted(peso_regiao.items(), key=lambda x: -x[1]):
        print(f"      {reg:<15} {v:>22,.0f} kg")
    print(f"      Tempo: {t3:.4f}s")

    # ── Filtro 4 ──
    print("\n[5/5] Filtro 4 — Federal × Estadual × Municipal (Brasil)")
    t = time.perf_counter()
    inspecao = filtro_inspecao(rows_ab)
    t4 = time.perf_counter() - t
    for tipo, v in sorted(inspecao.items(), key=lambda x: -x[1]):
        print(f"      {tipo:<10} {v:>22,.0f} cabeças")
    print(f"      Tempo: {t4:.4f}s")

    # ── Resumo ──
    total = time.perf_counter() - t0
    print("\n" + "=" * 60)
    print("   Resumo de Tempos")
    print("=" * 60)
    print(f"   Leitura do arquivo : {t_leitura:>8.2f}s")
    print(f"   Filtro 1           : {t1:>8.4f}s")
    print(f"   Filtro 2           : {t2:>8.4f}s")
    print(f"   Filtro 3           : {t3:>8.4f}s")
    print(f"   Filtro 4           : {t4:>8.4f}s")
    print(f"   TOTAL              : {total:>8.2f}s")
    print("=" * 60)

if __name__ == '__main__':
    main()
