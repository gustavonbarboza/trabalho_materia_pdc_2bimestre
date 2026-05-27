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
============================================================
   Análise Serial — Tabela 1092 IBGE
============================================================

[1/5] Lendo arquivo...
      21951 linhas (abatidos) | 21951 linhas (peso)
      Tempo de leitura: 42.30s

[2/5] Filtro 1 — Abate por Estado

[3/5] Filtro 2 — Evolução Anual

[4/5] Filtro 3 — Peso por Região

[5/5] Filtro 4 — Federal × Estadual × Municipal

  Filtro 1 — Abate por Estado (cabeças, 1997–2025)
  Estado                    Total de Cabeças  Rank
  Mato Grosso                  1.234.567.890  #1
  São Paulo                      987.654.321  #2
  ... (todos os 27 estados)

  Filtro 2 — Evolução Anual (Brasil)
  Ano    Total de Cabeças  Var. s/ ano ant.
  1997         45.123.456             —
  1998         47.890.123     +2.766.667
  ... (todos os 29 anos)

  Filtro 3 — Peso Total por Região (kg)
  Região          Peso Total (kg)  % do Brasil
  Centro-Oeste    432.109.876.543        38.1%
  ... (todas as 5 regiões)

  Filtro 4 — Federal × Estadual × Municipal (Brasil)
  Inspeção        Total de Cabeças  % do Total
  Federal              876.543.210       72.5%
  Estadual             234.567.890       19.4%
  Municipal             98.765.432        8.1%

============================================================
   Resumo de Tempos
============================================================
   Leitura do arquivo :    42.30s
   Filtro 1           :     8.10s
   Filtro 2           :     8.20s
   Filtro 3           :     8.05s
   Filtro 4           :     8.15s
   TOTAL              :    74.80s
============================================================
```
