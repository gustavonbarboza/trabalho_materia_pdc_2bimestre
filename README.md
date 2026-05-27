# Trabalho 2º Bimestre — Programação Paralela e Concorrente

Análise de dados do abate bovino no Brasil (IBGE — Tabela 1092) usando Python — implementação serial e paralelizada com threads.

---

## Dados

**Arquivo:** `tabela.csv`

**Fonte:** IBGE — *Número de informantes, Quantidade e Peso total das carcaças dos bovinos abatidos, no mês e no trimestre, por tipo de rebanho e tipo de inspeção.*

> ⚠️ **O arquivo CSV não está incluso no repositório** (8 GB — acima do limite do Git).
> Ele está disponível como asset na aba **[Google Drive](https://drive.google.com/file/d/1j5z0Tstp23AOCbXARNGulNlY9LMYXGNC/view?usp=sharing)** deste repositório.
>
> **Como obter:**
> 1. Acesse o **[Google Drive](https://drive.google.com/file/d/1j5z0Tstp23AOCbXARNGulNlY9LMYXGNC/view?usp=sharing)** e baixe o arquivo `.zip`
> 2. Descompacte o zip
> 3. Mova o arquivo `tabela.csv` para dentro desta pasta (raiz do projeto)
> 4. Execute normalmente com `python3 serial.py`

O arquivo contém 6 seções de variáveis, cada uma com dados trimestrais de **Q1 1997 a Q4 2025** (116 trimestres). Cada linha representa uma combinação de:

| Campo | Exemplos |
|---|---|
| Nível | `BR` (Brasil), `UF` (Estado), `MU` (Município) |
| Local | Brasil, São Paulo, Cuiabá... |
| Tipo de inspeção | Total, Federal, Estadual, Municipal |

As seções usadas neste trabalho são:
- **Animais abatidos (Cabeças)** — filtros 1, 2 e 4
- **Peso total das carcaças (Quilogramas)** — filtro 3

---

## Filtros Implementados

### Filtro 1 — Abate por Estado
Soma o total acumulado de cabeças abatidas por Unidade da Federação (UF), considerando apenas a inspeção `Total`. Permite identificar os estados com maior volume de abate no período.

### Filtro 2 — Evolução Anual (Brasil)
Agrega os dados mensais de cada ano para obter o total anual de cabeças abatidas no Brasil. Revela a tendência histórica do setor de 1997 a 2025, incluindo a variação em relação ao ano anterior.

### Filtro 3 — Peso Total por Região
Soma o peso das carcaças (em kg) de todos os estados de cada região geográfica brasileira:

| Região | Estados |
|---|---|
| Norte | RO, AC, AM, RR, PA, AP, TO |
| Nordeste | MA, PI, CE, RN, PB, PE, AL, SE, BA |
| Sudeste | MG, ES, RJ, SP |
| Sul | PR, SC, RS |
| Centro-Oeste | MS, MT, GO, DF |

### Filtro 4 — Federal × Estadual × Municipal
Compara o total de abates no Brasil separado por tipo de inspeção sanitária, mostrando o peso relativo de cada esfera de fiscalização ao longo de todo o período.

---

## Estrutura dos Arquivos

```
.
├── tabela.csv         # dados brutos (IBGE, 8 GB)
├── serial.py          # implementação serial
├── paralelizado.py    # implementação paralela com threads (2, 4, 6, 8, 12)
└── README.md
```

---

## Como Executar

> **Requisito:** Python 3.8+ (sem dependências externas — apenas biblioteca padrão)

```bash
# Versão serial
python3 serial.py

# Versão paralelizada (roda automaticamente com 2, 4, 6, 8 e 12 threads)
python3 paralelizado.py
```

Os scripts esperam que o arquivo CSV esteja na mesma pasta de onde são executados.

---

## serial.py e paralelizado.py

**`serial.py`** executa cada etapa de forma sequencial:

1. **Leitura** — percorre o arquivo linha a linha, coletando apenas as duas seções relevantes na memória.
2. **Filtro 1** → **Filtro 2** → **Filtro 3** → **Filtro 4**, um após o outro.
3. Ao final, imprime os resultados e o tempo gasto em cada etapa.

**`paralelizado.py`** faz a leitura uma única vez e roda os mesmos 4 filtros com 2, 4, 8 e 12 threads. A cada rodada exibe o cabeçalho com o número de threads, os resultados completos de todos os filtros (idênticos ao serial) e o tempo de processamento. Ao final, exibe a tabela de speedup comparando as configurações.

**Saída esperada (exemplo):**
```
==============================================================
   Análise Serial — Tabela 1092 IBGE
==============================================================

[1/5] Lendo arquivo...
      Percorrendo o CSV de 8 GB e carregando apenas as duas seções
      necessárias: 'Animais abatidos (Cabeças)' e
      'Peso total das carcaças (Quilogramas)'.
      -> 21.951 linhas carregadas para animais abatidos
      -> 21.951 linhas carregadas para peso das carcaças
      Tempo: 42.30s

[2/5] Filtro 1 — Abate por Estado
      Percorre todas as linhas no nível UF com inspeção Total.
      Para cada estado, soma os abates mês a mês (3 meses × 4
      trimestres × 29 anos = 348 leituras por linha) de 1997 a 2025.

      -> 27 estados encontrados. Ranking por volume de abate:

      Estado                    Total de Cabeças  Rank
      ------------------------- --------------------  ----
      Mato Grosso                  1.234.567.890  #1
      São Paulo                      987.654.321  #2
      Mato Grosso do Sul             876.543.210  #3
      ... (todos os 27 estados)

      Tempo: 8.10s

[3/5] Filtro 2 — Evolução Anual (Brasil)
      Agrupa os abates mensais por ano para o nível Brasil,
      inspeção Total. Calcula também a variação em relação ao
      ano anterior para revelar tendências de crescimento ou queda.

      -> 29 anos analisados (1997–2025):

      Ano    Total de Cabeças  Var. s/ ano ant.
      ------  --------------------  ----------------
        1997        45.123.456             —
        1998        47.890.123     +2.766.667
        1999        46.500.000     -1.390.123
        ... (todos os 29 anos)

      Tempo: 8.20s

[4/5] Filtro 3 — Peso Total das Carcaças por Região (kg)
      Usa a seção de peso das carcaças. Para cada estado (UF),
      inspeção Total, soma o peso em kg mês a mês e agrupa
      pelos 5 grupos regionais do Brasil.

      -> 5 regiões | peso total acumulado: 1.234.567.890.123 kg

      Região          Peso Total (kg)           % do Brasil
      --------------- ----------------------  ------------
      Centro-Oeste       432.109.876.543             38.1%
      Sudeste            310.987.654.321             27.4%
      Sul                210.123.456.789             18.5%
      Nordeste            98.765.432.100              8.7%
      Norte               82.345.678.901              7.3%

      Tempo: 8.05s

[5/5] Filtro 4 — Federal × Estadual × Municipal (Brasil)
      Filtra as linhas do nível Brasil separadas por tipo de
      inspeção sanitária (Federal, Estadual, Municipal).
      Mostra qual esfera fiscalizou mais cabeças no período total.

      -> total fiscalizado no período: 1.234.567.890 cabeças

      Inspeção        Total de Cabeças  % do Total
      ------------ ----------------------  ----------
      Federal              876.543.210       72.5%
      Estadual             234.567.890       19.4%
      Municipal             98.765.432        8.1%

      Tempo: 8.15s

==============================================================
   Resumo de Tempos
==============================================================
   Leitura do arquivo :    --s
   Filtro 1           :    --s
   Filtro 2           :    --s
   Filtro 3           :    --s
   Filtro 4           :    --s
   TOTAL              :    --s
==============================================================
```

---

## Resultados de Tempo

> Preencher após rodar nos dois scripts na máquina de testes.

### Tempos por configuração (segundos)

| Configuração | Leitura (s) | Filtro 1 (s) | Filtro 2 (s) | Filtro 3 (s) | Filtro 4 (s) | Total (s) |
|---|---|---|---|---|---|---|
| Serial        | -- | -- | -- | -- | -- | -- |
| 2 threads     | -- | --         | --         | --         | --         | -- |
| 4 threads     | -- | --         | --         | --         | --         | -- |
| 8 threads     | -- | --         | --         | --         | --         | -- |
| 12 threads    | -- | --         | --         | --         | --         | -- |

> Para o paralelizado, a leitura é feita uma única vez. Os filtros rodam em paralelo, então o tempo de processamento é o total das threads, não a soma individual.

### Speedup (processamento)

| Threads | Tempo proc. (s) | Speedup |
|---|---|---|
| 2  | -- | 1.00x |
| 4  | -- | --x   |
| 8  | -- | --x   |
| 12 | -- | --x   |
