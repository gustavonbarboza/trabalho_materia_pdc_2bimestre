# Trabalho 2º Bimestre — Programação Paralela e Concorrente

Análise de dados do abate bovino no Brasil (IBGE — Tabela 1092) usando Python — implementação serial e paralelizada com processos.

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
├── tabela.csv              # dados brutos (IBGE, 8 GB) — não versionado
├── serial.py               # implementação serial
├── paralelizado.py         # implementação paralela com processos (1, 2, 4, 8, 12)
├── rodar.py                # executa os dois scripts e salva os resultados
├── evidencias/             # saídas geradas automaticamente pelo rodar.py
│   ├── saida_serial_YYYY-MM-DD.txt
│   └── saida_paralelizado_YYYY-MM-DD.txt
└── README.md
```

---

## Como Executar

> **Requisito:** Python 3.8+ (sem dependências externas — apenas biblioteca padrão)

```bash
# Roda os dois scripts em sequência e salva os resultados em evidencias/
python3 rodar.py

# Ou rodar individualmente:
python3 serial.py
python3 paralelizado.py
```

Os scripts esperam que o arquivo `tabela.csv` esteja na mesma pasta de onde são executados.

### rodar.py

Executa `serial.py` e `paralelizado.py` em sequência, exibe a saída em tempo real no terminal e salva cada resultado em `evidencias/` com a data do dia no nome do arquivo (ex.: `saida_serial_2026-06-01.txt`). Se rodar duas vezes no mesmo dia, sobrescreve o arquivo do dia. Se rodar em outro dia, cria um arquivo novo — o histórico fica preservado.

---

## serial.py e paralelizado.py

### serial.py

Executa cada etapa de forma sequencial:

1. **Leitura** — percorre o arquivo linha a linha, coletando apenas as duas seções relevantes na memória.
2. **Filtro 1** → **Filtro 2** → **Filtro 3** → **Filtro 4**, um após o outro.
3. Ao final, imprime os resultados e o tempo de cada etapa.

### paralelizado.py

> **Por que processos e não threads?**
> Em Python, threads não paralelizam trabalho de CPU por causa do **GIL (Global Interpreter Lock)** — apenas uma thread executa código Python por vez. Testado em máquina real: 2 threads = 135s, 4 = 130s, 8 = 138s, 12 = 143s. Praticamente sem melhora.
> `multiprocessing` cria processos independentes, cada um com seu próprio GIL, permitindo paralelismo real em múltiplos núcleos.

> **Por que os workers leem o arquivo diretamente?**
> Passar os dados brutos entre processos exige serialização (pickle). Com ~1.2 GB de listas Python, o pickle trava o programa antes mesmo de começar a processar.
> A solução: o processo principal faz um **pré-scan** do arquivo para registrar apenas os **offsets em bytes** de cada seção. Cada worker recebe 4 inteiros (~50 bytes via pickle) e abre o arquivo por conta própria, lendo só o seu trecho. Sem gargalo de serialização.

**Fluxo do paralelizado.py:**

```
[1] Pré-scan (~42s, único)
    Leitura sequencial do CSV para encontrar os offsets em bytes
    das seções 'Animais abatidos' e 'Peso das carcaças'.

[2] Para cada N em [2, 4, 8, 12]:
    ├── Divide cada seção em N fatias (alinhadas a linhas completas)
    ├── Pool de N processos: cada um lê sua fatia do disco + calcula os 4 filtros
    ├── Processo principal agrega os N resultados parciais
    └── Exibe filtros + tempo de processamento paralelo

[3] Tabela de speedup comparando as 4 configurações
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

### serial.py

| Etapa | Tempo (s) |
|---|---|
| Leitura do arquivo | 118.05s |
| Filtro 1 | 45.23s |
| Filtro 2 | 33.23s |
| Filtro 3 | 54.95s |
| Filtro 4 | 54.66s |
| **TOTAL** | 306.22s |

### paralelizado.py

O pré-scan é feito **uma única vez** antes de todas as rodadas. O tempo de processamento é o das N tarefas rodando em paralelo.

| Configuração | Pré-scan (s) | Processamento (s) | Total (s) |
|---|---|---|---|
| 2 processos  | 41.29s | 18.68s | 59.97s |
| 4 processos  | 41.29s | 10.57s | 51.86s |
| 8 processos  | 41.29s | 6.83s | 48.12s |
| 12 processos | 41.29s | 6.16s | 47.45s |

### Speedup — Total (leitura + processamento)

Referência para o speedup paralelo: **1 processo** (mesmo algoritmo, sem paralelismo).
Referência para speedup vs serial: **serial.py** (algoritmo diferente, 4 passes sobre os dados).

| Configuração | Leitura (s) | Processamento (s) | Total (s) | Speedup vs Serial |
|---|---|---|---|---|
| Serial        | 118.05 | 188.07 | 306.22 | ref |
| 1 processo    |  41.29 |   ~37  |  ~78   | ~3.9x |
| 2 processos   |  41.29 |  18.68 |  59.97 | 5.11x |
| 4 processos   |  41.29 |  10.57 |  51.86 | 5.90x |
| 8 processos   |  41.29 |   6.83 |  48.12 | 6.36x |
| 12 processos  |  41.29 |   6.16 |  47.45 | 6.45x |

### Speedup de Processamento (referência: 1 processo)

| Processos | Tempo proc. (s) | Speedup |
|---|---|---|
| 1  | ~37   | 1.00x |
| 2  | 18.68 | ~2.0x |
| 4  | 10.57 | ~3.5x |
| 8  | 6.83  | ~5.4x |
| 12 | 6.16  | ~6.0x |

> **Por que a leitura do paralelo (41s) é mais rápida que a do serial (118s)?**
> O pré-scan apenas registra os offsets em bytes — não armazena linhas na RAM.
> O serial carrega 86.864 linhas × ~2.800 colunas de strings Python na memória.

> **Por que o speedup satura em ~6x com 8–12 processos?**
> O i5-12500 tem **6 núcleos físicos**. Até 4–6 processos o ganho é quase linear.
> Com 8+ processos, os núcleos extras compartilham os mesmos núcleos físicos via hyperthreading — e o disco começa a ser o gargalo com múltiplos leitores simultâneos.
