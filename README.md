# Trabalho 2º Bimestre — Programação Paralela e Concorrente

Análise de dados do abate bovino no Brasil (IBGE — Tabela 1092) usando Python — implementação serial.

---

## Dados

**Arquivo:** `tabela1092_2GB.csv` (~2 GB, ~131.765 linhas)

**Fonte:** IBGE — *Número de informantes, Quantidade e Peso total das carcaças dos bovinos abatidos, no mês e no trimestre, por tipo de rebanho e tipo de inspeção.*

> ⚠️ **O arquivo CSV não está incluso no repositório** (2 GB — acima do limite do Git).
> Ele está disponível como asset na aba **[Releases](../../releases)** deste repositório.
>
> **Como obter:**
> 1. Acesse a aba **Releases** e baixe o arquivo `.zip`
> 2. Descompacte o zip
> 3. Mova o arquivo `tabela1092_2GB.csv` para dentro desta pasta (raiz do projeto)
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
├── tabela1092_2GB.csv   # dados brutos (IBGE)
├── serial.py            # implementação serial
└── README.md
```

---

## Como Executar

> **Requisito:** Python 3.8+ (sem dependências externas — apenas biblioteca padrão)

```bash
python3 serial.py
```

O script espera que o arquivo CSV esteja na mesma pasta de onde é executado.

---

## serial.py

Executa cada etapa de forma sequencial:

1. **Leitura** — percorre o arquivo linha a linha, coletando apenas as duas seções relevantes na memória.
2. **Filtro 1** → **Filtro 2** → **Filtro 3** → **Filtro 4**, um após o outro.
3. Ao final, imprime os resultados e o tempo gasto em cada etapa.

**Saída esperada (exemplo):**
```
==============================================================
   Análise Serial — Tabela 1092 IBGE
==============================================================

[1/5] Lendo arquivo...
      Percorrendo o CSV de 2 GB e carregando apenas as duas seções
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
   Leitura do arquivo :    42.30s
   Filtro 1           :     8.10s
   Filtro 2           :     8.20s
   Filtro 3           :     8.05s
   Filtro 4           :     8.15s
   TOTAL              :    74.80s
==============================================================
```
