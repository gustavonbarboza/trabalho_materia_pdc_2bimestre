# Trabalho 2º Bimestre — Programação Paralela e Distribuída

Análise de dados do abate bovino no Brasil (IBGE — Tabela 1092) usando Python — implementação paralelizada com processos.

---

## Dados

**Arquivo:** `tabela.csv`

**Fonte:** IBGE — *Número de informantes, Quantidade e Peso total das carcaças dos bovinos abatidos, no mês e no trimestre, por tipo de rebanho e tipo de inspeção.*

> ⚠️ **O arquivo CSV não está incluso no repositório** (8 GB — acima do limite do Git).
> Disponível para download no **[Google Drive](https://drive.google.com/file/d/1j5z0Tstp23AOCbXARNGulNlY9LMYXGNC/view?usp=sharing)**.
>
> **Como obter:**
> 1. Acesse o link acima e baixe o arquivo `.zip`
> 2. Descompacte o zip
> 3. Mova o arquivo `tabela.csv` para dentro desta pasta (raiz do projeto)
> 4. Execute com `python3 paralelizado.py`

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
├── tabela.csv              # dados brutos (IBGE, 8 GB) — não versionado
├── paralelizado.py         # implementação paralela com processos (1, 2, 4, 8, 12)
├── evidencias/             # saídas de execuções anteriores
│   └── saida_paralelizado_YYYY-MM-DD.txt
└── README.md
```

---

## Como Executar

> **Requisito:** Python 3.8+ (sem dependências externas — apenas biblioteca padrão)

```bash
python3 paralelizado.py
```

O script espera que o arquivo `tabela.csv` esteja na mesma pasta de onde é executado.

---

## paralelizado.py

> **Por que processos e não threads?**
> Em Python, threads não paralelizam trabalho de CPU por causa do **GIL (Global Interpreter Lock)** — apenas uma thread executa código Python por vez. Testado em máquina real: 2 threads = 135s, 4 = 130s, 8 = 138s, 12 = 143s. Praticamente sem melhora.
> `multiprocessing` cria processos independentes, cada um com seu próprio GIL, permitindo paralelismo real em múltiplos núcleos.

> **Por que os workers leem o arquivo diretamente?**
> Passar os dados brutos entre processos exige serialização (pickle). Com ~1.2 GB de listas Python, o pickle trava o programa antes mesmo de começar a processar.
> A solução: o processo principal faz um **pré-scan** do arquivo para registrar apenas os **offsets em bytes** de cada seção. Cada worker recebe 4 inteiros (~50 bytes via pickle) e abre o arquivo por conta própria, lendo só o seu trecho. Sem gargalo de serialização.

> **Por que filtrar antes de calcular?**
> A função `calcular_por_ano` executa 348 leituras de coluna por linha. O código anterior chamava essa função para **todas** as linhas da seção e só depois descartava as irrelevantes (nível `MU`, inspeções não usadas). O filtro agora é aplicado **antes** do cálculo: linhas que não contribuem para nenhum resultado recebem um `continue` imediato, eliminando o trabalho desnecessário e reduzindo significativamente o tempo de processamento por processo.

**Fluxo do paralelizado.py:**

```
[1] Pré-scan (~41s, único)
    Leitura sequencial do CSV para encontrar os offsets em bytes
    das seções 'Animais abatidos' e 'Peso das carcaças'.

[2] Para cada N em [1, 2, 4, 8, 12]:
    ├── Divide cada seção em N fatias (alinhadas a linhas completas)
    ├── Pool de N processos: cada um lê sua fatia do disco + calcula os 4 filtros
    │   (apenas linhas relevantes são processadas — filtro antecipado)
    ├── Processo principal agrega os N resultados parciais
    └── Exibe filtros + tempo de processamento paralelo

[3] Tabela de speedup comparando as 5 configurações
```

---

## Configuração da Máquina de Testes

| Componente | Especificação |
|---|---|
| **Processador** | Intel Core i5-12500 |
| **Núcleos / Threads** | 6 núcleos físicos / 12 threads |
| **RAM** | 16 GB |
| **GPU** | Intel UHD Graphics 770 |
| **Sistema Operacional** | Windows |
| **Python** | 3.13 |

> Os resultados de tempo abaixo foram medidos nesta máquina.

---

## Resultados de Tempo

### Referência Serial (medido antes da otimização)

| Etapa | Tempo (s) |
|---|---|
| Leitura do arquivo | 135.12s |
| Filtro 1 | 54.69s |
| Filtro 2 | 31.82s |
| Filtro 3 | 61.77s |
| Filtro 4 | 49.89s |
| **TOTAL** | **333.51s** |

### paralelizado.py — 18/06/2026

O pré-scan é feito **uma única vez** antes de todas as rodadas. O tempo de processamento é o das N tarefas rodando em paralelo.

| Configuração | Pré-scan (s) | Processamento (s) | Total (s) |
|---|---|---|---|
| 1 processo   | 41.41 | 14.53 | 55.94 |
| 2 processos  | 41.41 |  7.60 | 49.01 |
| 4 processos  | 41.41 |  4.58 | 45.99 |
| 8 processos  | 41.41 |  2.87 | 44.29 |
| 12 processos | 41.41 |  2.31 | 43.73 |

### Speedup — Total (leitura + processamento)

| Configuração | Leitura (s) | Processamento (s) | Total (s) | Speedup vs Serial |
|---|---|---|---|---|
| (Serial)      |  41.41 |  14.53 |  55.94 | 5.96x |
| 2 processos   |  41.41 |   7.60 |  49.01 | 6.80x |
| 4 processos   |  41.41 |   4.58 |  45.99 | 7.25x |
| 8 processos   |  41.41 |   2.87 |  44.29 | 7.53x |
| 12 processos  |  41.41 |   2.31 |  43.73 | 7.63x |

### Speedup de Processamento (referência: 1 processo = 14.53s)

| Processos | Tempo proc. (s) | Speedup |
|---|---|---|
| 1  | 14.53 | 1.00x |
| 2  |  7.60 | 1.91x |
| 4  |  4.58 | 3.17x |
| 8  |  2.87 | 5.06x |
| 12 |  2.31 | 6.28x |

> **Por que a leitura do paralelo (41s) é mais rápida que a do serial (135s)?**
> O pré-scan apenas registra os offsets em bytes — não armazena linhas na RAM.
> O serial carregava 86.864 linhas × ~2.800 colunas de strings Python na memória.

> **Por que o speedup satura em ~7.6x com 12 processos?**
> O i5-12500 tem **6 núcleos físicos**. Com 8+ processos os núcleos extras compartilham os mesmos núcleos físicos via hyperthreading — e o disco passa a ser o gargalo com múltiplos leitores simultâneos. O pré-scan fixo de ~41s também limita o speedup total pelo limite de Amdahl.
