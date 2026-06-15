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

### serial.py — 15/06/2026

| Etapa | Tempo (s) |
|---|---|
| Leitura do arquivo | 135.12s |
| Filtro 1 | 54.69s |
| Filtro 2 | 31.82s |
| Filtro 3 | 61.77s |
| Filtro 4 | 49.89s |
| **TOTAL** | **333.51s** |

### paralelizado.py — 15/06/2026

O pré-scan é feito **uma única vez** antes de todas as rodadas. O tempo de processamento é o das N tarefas rodando em paralelo.

| Configuração | Pré-scan (s) | Processamento (s) | Total (s) |
|---|---|---|---|
| 1 processo   | 44.60s | 35.08s | 79.68s |
| 2 processos  | 44.60s | 18.61s | 63.21s |
| 4 processos  | 44.60s | 10.45s | 55.05s |
| 8 processos  | 44.60s |  6.79s | 51.38s |
| 12 processos | 44.60s |  5.98s | 50.58s |

### Speedup — Total (leitura + processamento)

| Configuração | Leitura (s) | Processamento (s) | Total (s) | Speedup vs Serial |
|---|---|---|---|---|
| Serial        | 135.12 | 198.17 | 333.51 | ref   |
| 1 processo    |  44.60 |  35.08 |  79.68 | 4.19x |
| 2 processos   |  44.60 |  18.61 |  63.21 | 5.28x |
| 4 processos   |  44.60 |  10.45 |  55.05 | 6.06x |
| 8 processos   |  44.60 |   6.79 |  51.38 | 6.49x |
| 12 processos  |  44.60 |   5.98 |  50.58 | 6.59x |

### Speedup de Processamento (referência: 1 processo = 35.08s)

| Processos | Tempo proc. (s) | Speedup |
|---|---|---|
| 1  | 35.08 | 1.00x |
| 2  | 18.61 | 1.88x |
| 4  | 10.45 | 3.36x |
| 8  |  6.79 | 5.17x |
| 12 |  5.98 | 5.86x |

> **Por que a leitura do paralelo (44s) é mais rápida que a do serial (135s)?**
> O pré-scan apenas registra os offsets em bytes — não armazena linhas na RAM.
> O serial carrega 86.864 linhas × ~2.800 colunas de strings Python na memória.

> **Por que o speedup satura em ~6x com 8–12 processos?**
> O i5-12500 tem **6 núcleos físicos**. Até 4–6 processos o ganho é quase linear.
> Com 8+ processos, os núcleos extras compartilham os mesmos núcleos físicos via hyperthreading — e o disco começa a ser o gargalo com múltiplos leitores simultâneos.
