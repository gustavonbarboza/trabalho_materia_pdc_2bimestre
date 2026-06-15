"""
paralelizado.py

Por que NAO usamos threads?
  Threads (threading.Thread) NAO paralelizam trabalho de CPU em Python porque
  o GIL (Global Interpreter Lock) permite que apenas uma thread execute
  codigo Python por vez. Resultado: 2, 4, 8 ou 12 threads rodam em fila —
  o tempo nao melhora (confirmado nos testes: 135s / 130s / 138s / 143s).

Por que usamos multiprocessing?
  Cada processo tem seu proprio interpretador e seu proprio GIL — paralelismo
  real em nucleos distintos do CPU.

Por que os workers leem o arquivo diretamente?
  A abordagem anterior passava ~1.2 GB de listas Python via pickle para os
  processos filhos. Serializar esse volume trava o programa antes de comecar.
  Aqui, cada worker recebe apenas 4 inteiros (offsets em bytes) e abre o
  arquivo por conta propria — sem gargalo de serializacao.

Fluxo:
  1. Pre-scan (processo principal, ~42s): le o CSV uma vez para localizar
     em bytes onde comeца e termina cada secao relevante.
  2. Para cada N em [2, 4, 8, 12]:
     - Divide os intervalos em N fatias alinhadas a linhas.
     - Pool de N processos: cada um le sua fatia e calcula os 4 filtros.
     - Processo principal agrega os resultados parciais e exibe.
  3. Tabela de speedup ao final.

Compativel com Windows (spawn), Linux e macOS.
"""

import time
import multiprocessing as mp
from collections import defaultdict

CSV_FILE      = 'tabela.csv'
THREAD_COUNTS = [1, 2, 4, 8, 12]

# Tempos medidos no serial.py na mesma maquina (atualizar se rodar em outro PC)
# serial.py: leitura 118.05s | filtro1 45.23s | filtro2 33.23s | filtro3 54.95s | filtro4 54.66s
SERIAL_LEITURA = 118.05   # segundos — leitura e armazenamento de todas as linhas na RAM
SERIAL_PROC    = 188.07   # segundos — soma dos 4 filtros (45.23 + 33.23 + 54.95 + 54.66)
SERIAL_TOTAL   = 306.22   # segundos — leitura + 4 filtros em sequencia

NUM_QUARTERS = 116     # Q1 1997 -> Q4 2025
START_YEAR   = 1997
NUM_YEARS    = 29

STATE_REGIONS = {
    'Rondonia': 'Norte',       'Acre': 'Norte',            'Amazonas': 'Norte',
    'Roraima': 'Norte',        'Para': 'Norte',             'Amapa': 'Norte',
    'Tocantins': 'Norte',
    'Maranhao': 'Nordeste',    'Piaui': 'Nordeste',         'Ceara': 'Nordeste',
    'Rio Grande do Norte': 'Nordeste', 'Paraiba': 'Nordeste', 'Pernambuco': 'Nordeste',
    'Alagoas': 'Nordeste',     'Sergipe': 'Nordeste',       'Bahia': 'Nordeste',
    'Minas Gerais': 'Sudeste', 'Espirito Santo': 'Sudeste', 'Rio de Janeiro': 'Sudeste',
    'Sao Paulo': 'Sudeste',
    'Parana': 'Sul',           'Santa Catarina': 'Sul',     'Rio Grande do Sul': 'Sul',
    'Mato Grosso do Sul': 'Centro-Oeste', 'Mato Grosso': 'Centro-Oeste',
    'Goias': 'Centro-Oeste',   'Distrito Federal': 'Centro-Oeste',
    # Com acentos (caso o CSV use)
    'Rondonia': 'Norte',       'Para': 'Norte',             'Amapa': 'Norte',
    'Maranhao': 'Nordeste',    'Piaui': 'Nordeste',         'Ceara': 'Nordeste',
    'Paraiba': 'Nordeste',     'Espirito Santo': 'Sudeste', 'Sao Paulo': 'Sudeste',
    'Parana': 'Sul',           'Goias': 'Centro-Oeste',
    # Versoes com unicode
    'Rondônia': 'Norte',  'Pará': 'Norte',        'Amapá': 'Norte',
    'Maranhão': 'Nordeste', 'Piauí': 'Nordeste',  'Ceará': 'Nordeste',
    'Paraíba': 'Nordeste', 'Espírito Santo': 'Sudeste',
    'São Paulo': 'Sudeste', 'Paraná': 'Sul',
    'Goiás': 'Centro-Oeste',
}

# ─── Utilitários (idênticos ao serial) ───────────────────────────────────────

def _decode(raw_bytes):
    """Decodifica bytes para string, com fallback para latin-1."""
    try:
        return raw_bytes.decode('utf-8').rstrip('\n')
    except UnicodeDecodeError:
        return raw_bytes.decode('latin-1').rstrip('\n')

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
    Soma os animais por ano usando os dados de CADA MES individualmente
    (3 meses x 4 trimestres x 29 anos = 348 leituras por linha).
    Coluna do mes M no trimestre Q:  3 + Q*24 + M*6   (M = 1, 2, 3)
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

# ─── Pré-scan: localiza as seções no arquivo ──────────────────────────────────

def encontrar_limites_secoes(csv_file):
    """
    Leitura sequencial em modo binario para registrar apenas os offsets em bytes
    do inicio e fim dos dados em cada secao relevante.
    Nao armazena conteudo das linhas — usa memoria minima (~algumas centenas de bytes).
    Retorna: (ab_inicio, ab_fim, pe_inicio, pe_fim)
    """
    ab_inicio = ab_fim = None
    pe_inicio = pe_fim = None
    secao_atual = None
    cabecalhos  = 0

    with open(csv_file, 'rb') as f:
        while True:
            pos = f.tell()           # offset ANTES de ler a linha atual
            raw = f.readline()
            if not raw:              # EOF
                eof = f.tell()
                if secao_atual == 'abatidos' and ab_fim is None:
                    ab_fim = eof
                elif secao_atual == 'peso' and pe_fim is None:
                    pe_fim = eof
                break

            linha = _decode(raw)
            if not linha:
                continue

            primeiro = linha.split(';')[0].strip('"')

            # Linha de cabecalho de secao — identifica qual secao começa
            if primeiro.startswith('Vari'):
                # Fecha a secao anterior
                if secao_atual == 'abatidos' and ab_fim is None:
                    ab_fim = pos
                elif secao_atual == 'peso' and pe_fim is None:
                    pe_fim = pos

                if 'Animais abatidos' in linha:
                    secao_atual = 'abatidos'
                elif 'Peso total' in linha and ('carca' in linha or 'Quilo' in linha):
                    secao_atual = 'peso'
                else:
                    secao_atual = None
                cabecalhos = 0
                continue

            if secao_atual is None:
                continue
            if cabecalhos < 4:       # pula os 4 cabecalhos de coluna
                cabecalhos += 1
                continue

            # Primeira linha de dados desta secao
            if secao_atual == 'abatidos' and ab_inicio is None:
                ab_inicio = pos
            elif secao_atual == 'peso' and pe_inicio is None:
                pe_inicio = pos

    return ab_inicio, ab_fim, pe_inicio, pe_fim

# ─── Divisão dos intervalos em chunks alinhados a linhas ─────────────────────

def dividir_em_chunks_bytes(csv_file, inicio, fim, n):
    """
    Divide o intervalo [inicio, fim) em n fatias cujas fronteiras coincidem
    com o inicio de uma linha completa — nunca corta no meio de uma linha.
    """
    tamanho = fim - inicio
    chunks   = []
    pos_atual = inicio

    with open(csv_file, 'rb') as f:
        for i in range(n):
            chunk_start = pos_atual
            if i == n - 1:
                chunk_end = fim
            else:
                target = inicio + (i + 1) * tamanho // n
                f.seek(target)
                f.readline()                       # avanca ate o proximo \n
                chunk_end = min(f.tell(), fim)
            chunks.append((chunk_start, chunk_end))
            pos_atual = chunk_end

    return chunks

# ─── Worker: le e processa sua fatia direto do arquivo ───────────────────────

def worker_pool(args):
    """
    Recebe apenas 5 valores pequenos: caminho do arquivo + 4 offsets inteiros.
    O pickle transfere ~50 bytes por processo (em vez de ~300 MB de listas).

    Cada processo:
      - Abre o arquivo de forma independente
      - Le somente seu trecho da secao 'abatidos' e seu trecho da secao 'peso'
      - Calcula os 4 filtros sobre essas linhas
      - Retorna 4 dicionarios parciais para o processo principal agregar
    """
    csv_file, ab_start, ab_end, pe_start, pe_end = args

    r1 = defaultdict(float)   # abate por estado
    r2 = defaultdict(float)   # evolucao anual
    r3 = defaultdict(float)   # peso por regiao
    r4 = defaultdict(float)   # tipo de inspecao

    # ── Seção abatidos ────────────────────────────────────────────────────────
    with open(csv_file, 'rb') as f:
        f.seek(ab_start)
        while f.tell() < ab_end:
            raw = f.readline()
            if not raw:
                break
            linha = _decode(raw)
            if not linha:
                continue
            row = linha.split(';')
            if len(row) < 3:
                continue
            row[0] = row[0].strip('"')
            row[1] = row[1].strip('"')
            row[2] = row[2].strip('"')

            anuais = calcular_por_ano(row)

            if row[0] == 'UF' and row[2] == 'Total':
                r1[row[1]] += sum(anuais.values())

            if row[0] == 'BR' and row[2] == 'Total':
                for ano, v in anuais.items():
                    r2[ano] += v

            if row[0] == 'BR' and row[2] in ('Federal', 'Estadual', 'Municipal'):
                r4[row[2]] += sum(anuais.values())

    # ── Seção peso ────────────────────────────────────────────────────────────
    with open(csv_file, 'rb') as f:
        f.seek(pe_start)
        while f.tell() < pe_end:
            raw = f.readline()
            if not raw:
                break
            linha = _decode(raw)
            if not linha:
                continue
            row = linha.split(';')
            if len(row) < 3:
                continue
            row[0] = row[0].strip('"')
            row[1] = row[1].strip('"')
            row[2] = row[2].strip('"')

            anuais = calcular_por_ano(row)
            if row[0] == 'UF' and row[2] == 'Total':
                regiao = STATE_REGIONS.get(row[1])
                if regiao:
                    r3[regiao] += sum(anuais.values())

    return dict(r1), dict(r2), dict(r3), dict(r4)

# ─── Execução paralela ────────────────────────────────────────────────────────

def rodar_com_n_processos(csv_file, chunks_ab, chunks_pe, n):
    # Cada elemento de args: (csv_file, ab_start, ab_end, pe_start, pe_end)
    args = [
        (csv_file, ab[0], ab[1], pe[0], pe[1])
        for ab, pe in zip(chunks_ab, chunks_pe)
    ]

    with mp.Pool(processes=n) as pool:
        resultados = pool.map(worker_pool, args)

    # Agrega os dicionarios parciais de cada processo
    r1, r2, r3, r4 = (defaultdict(float) for _ in range(4))
    for p1, p2, p3, p4 in resultados:
        for k, v in p1.items(): r1[k] += v
        for k, v in p2.items(): r2[k] += v
        for k, v in p3.items(): r3[k] += v
        for k, v in p4.items(): r4[k] += v

    return r1, r2, r3, r4

# ─── Exibição dos filtros ─────────────────────────────────────────────────────

def exibir_filtros(r1, r2, r3, r4):
    print("\n[2/5] Filtro 1 - Abate por Estado")
    print("      Percorre todas as linhas no nivel UF com inspecao Total.")
    print("      Para cada estado, soma os abates mes a mes (3 meses x 4")
    print("      trimestres x 29 anos = 348 leituras por linha) de 1997 a 2025.")
    print(f"\n      -> {len(r1)} estados encontrados. Ranking por volume de abate:\n")
    print(f"      {'Estado':<25} {'Total de Cabecas':>20}  Rank")
    print(f"      {'-'*25} {'-'*20}  ----")
    for rank, (est, v) in enumerate(sorted(r1.items(), key=lambda x: -x[1]), 1):
        print(f"      {est:<25} {v:>20,.0f}  #{rank}")

    print("\n[3/5] Filtro 2 - Evolucao Anual (Brasil)")
    print("      Agrupa os abates mensais por ano para o nivel Brasil,")
    print("      inspecao Total. Calcula tambem a variacao em relacao ao")
    print("      ano anterior para revelar tendencias de crescimento ou queda.")
    anos = sorted(r2)
    if anos:
        print(f"\n      -> {len(anos)} anos analisados ({anos[0]}-{anos[-1]}):\n")
        print(f"      {'Ano':>6}  {'Total de Cabecas':>20}  {'Var. s/ ano ant.':>16}")
        print(f"      {'------':>6}  {'-'*20}  {'-'*16}")
        for i, ano in enumerate(anos):
            v   = r2[ano]
            var = "    -" if i == 0 else f"{'+'if v-r2[anos[i-1]]>=0 else ''}{v-r2[anos[i-1]]:,.0f}"
            print(f"      {ano:>6}  {v:>20,.0f}  {var:>16}")

    print("\n[4/5] Filtro 3 - Peso Total das Carcacas por Regiao (kg)")
    print("      Usa a secao de peso das carcacas. Para cada estado (UF),")
    print("      inspecao Total, soma o peso em kg mes a mes e agrupa")
    print("      pelos 5 grupos regionais do Brasil.")
    tg = sum(r3.values())
    print(f"\n      -> {len(r3)} regioes | peso total acumulado: {tg:,.0f} kg\n")
    print(f"      {'Regiao':<15} {'Peso Total (kg)':>22}  {'% do Brasil':>12}")
    print(f"      {'-'*15} {'-'*22}  {'-'*12}")
    for reg, v in sorted(r3.items(), key=lambda x: -x[1]):
        print(f"      {reg:<15} {v:>22,.0f}  {(v/tg*100) if tg else 0:>11.1f}%")

    print("\n[5/5] Filtro 4 - Federal x Estadual x Municipal (Brasil)")
    print("      Filtra as linhas do nivel Brasil separadas por tipo de")
    print("      inspecao sanitaria (Federal, Estadual, Municipal).")
    print("      Mostra qual esfera fiscalizou mais cabecas no periodo total.")
    ti = sum(r4.values())
    print(f"\n      -> total fiscalizado no periodo: {ti:,.0f} cabecas\n")
    print(f"      {'Inspecao':<12} {'Total de Cabecas':>22}  {'% do Total':>10}")
    print(f"      {'-'*12} {'-'*22}  {'-'*10}")
    for tipo, v in sorted(r4.items(), key=lambda x: -x[1]):
        print(f"      {tipo:<12} {v:>22,.0f}  {(v/ti*100) if ti else 0:>9.1f}%")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("   Analise Paralela (Processos) - Tabela 1092 IBGE")
    print("=" * 62)

    # Pre-scan: uma unica leitura sequencial para achar os offsets das secoes.
    # Armazena apenas 4 inteiros — sem guardar conteudo das linhas na RAM.
    print("\n[1/5] Pre-scan: localizando secoes no arquivo...")
    print("      Leitura sequencial do CSV de 8 GB para registrar os")
    print("      offsets em bytes de 'Animais abatidos' e 'Peso das carcacas'.")
    t_scan = time.perf_counter()
    ab_inicio, ab_fim, pe_inicio, pe_fim = encontrar_limites_secoes(CSV_FILE)
    t_scan = time.perf_counter() - t_scan

    if None in (ab_inicio, ab_fim, pe_inicio, pe_fim):
        print("ERRO: secoes nao encontradas. Verifique o arquivo CSV.")
        return

    print(f"      -> abatidos : {(ab_fim - ab_inicio) / 1_000_000:,.0f} MB de dados")
    print(f"      -> peso     : {(pe_fim - pe_inicio) / 1_000_000:,.0f} MB de dados")
    print(f"      Tempo de pre-scan: {t_scan:.2f}s")

    tempos = {}

    for n in THREAD_COUNTS:
        print(f"\n\n{'=' * 62}")
        print(f"{'=' * 20}  {n} PROCESSOS  {'=' * 20}")
        print(f"{'=' * 62}")

        # Divide cada secao em n fatias alinhadas a linhas
        chunks_ab = dividir_em_chunks_bytes(CSV_FILE, ab_inicio, ab_fim, n)
        chunks_pe = dividir_em_chunks_bytes(CSV_FILE, pe_inicio, pe_fim, n)

        t0 = time.perf_counter()
        r1, r2, r3, r4 = rodar_com_n_processos(CSV_FILE, chunks_ab, chunks_pe, n)
        t_proc = time.perf_counter() - t0

        tempos[n] = t_proc

        exibir_filtros(r1, r2, r3, r4)

        print(f"\n{'=' * 62}")
        print(f"   Resumo - {n} processos")
        print(f"{'=' * 62}")
        print(f"   Pre-scan (unico, fixo)  : {t_scan:>8.2f}s")
        print(f"   Processamento paralelo  : {t_proc:>8.2f}s")
        print(f"   TOTAL                   : {t_scan + t_proc:>8.2f}s")
        print(f"{'=' * 62}")

    # ── Tabela de Speedup ─────────────────────────────────────────────────────
    # Referencia: 1 processo (paralelo desativado, mesmo algoritmo dos workers).
    # Mostra como o tempo cai ao adicionar processos — e onde satura.
    t_ref_proc  = tempos[1]           # processamento com 1 processo (baseline)
    t_ref_total = t_scan + t_ref_proc # total com 1 processo

    print(f"\n\n{'=' * 62}")
    print("   Comparativo de Speedup — Total (leitura + processamento)")
    print(f"{'=' * 62}")
    print(f"   {'Configuracao':<16}  {'Leitura (s)':>11}  {'Proc. (s)':>10}  {'Total (s)':>10}  {'Speedup':>8}")
    print(f"   {'-'*16}  {'-'*11}  {'-'*10}  {'-'*10}  {'-'*8}")
    print(f"   {'Serial':<16}  {SERIAL_LEITURA:>11.2f}  {SERIAL_PROC:>10.2f}  {SERIAL_TOTAL:>10.2f}  {'ref':>8}")
    for n in THREAD_COUNTS:
        total = t_scan + tempos[n]
        sp    = SERIAL_TOTAL / total
        print(f"   {f'{n} processo(s)':<16}  {t_scan:>11.2f}  {tempos[n]:>10.2f}  {total:>10.2f}  {sp:>7.2f}x")
    print(f"{'=' * 62}")

    # ── Gráfico ASCII de processamento paralelo ───────────────────────────────
    BAR_MAX = 38
    print(f"\n\n{'=' * 62}")
    print("   Tempo de processamento por numero de processos")
    print("   (quanto menor a barra, mais rapido — mostra onde satura)")
    print(f"{'=' * 62}")
    for n in THREAD_COUNTS:
        t  = tempos[n]
        sp = t_ref_proc / t
        barra = '#' * max(1, round(t / t_ref_proc * BAR_MAX))
        print(f"   {n:>2} proc  |{barra:<{BAR_MAX}}  {t:>6.2f}s  ({sp:.2f}x)")
    print(f"{'=' * 62}")
    print()
    print("   Referencia: 1 processo = base 1.00x")
    print(f"   Pre-scan fixo: {t_scan:.1f}s | Serial: {SERIAL_TOTAL:.1f}s")
    print("=" * 62)


if __name__ == '__main__':
    main()
