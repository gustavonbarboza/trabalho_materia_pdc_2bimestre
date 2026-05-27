# Trabalho 2º Bimestre — Programação Paralela e Concorrente

Análise de dados do abate bovino no Brasil (IBGE — Tabela 1092) usando Python, comparando uma implementação **serial** com uma **paralelizada com threads**.

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
Agrega os 4 trimestres de cada ano para obter o total anual de cabeças abatidas no Brasil. Revela a tendência histórica do setor de 1997 a 2025.

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
├── paralelizado.py      # implementação paralela com threads
└── README.md
```

---

## Como Executar

> **Requisito:** Python 3.8+ (sem dependências externas — apenas biblioteca padrão)

```bash
# Versão serial (1ª entrega)
python3 serial.py

# Versão paralela (2ª entrega)
python3 paralelizado.py
```

Ambos os scripts esperam que o arquivo CSV esteja na mesma pasta de onde são executados.

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
      Estado                    Total de Cabeças  Rank
      ------------------------- --------------------  ----
      Mato Grosso                    1.234.567.890  #1
      São Paulo                        987.654.321  #2
      ... (todos os 27 estados)
      Tempo: 0.8321s

[3/5] Filtro 2 — Evolução Anual (Brasil)
      Ano    Total de Cabeças  Var. s/ ano ant.
      ------  --------------------  ----------------
      1997          45.123.456             —
      1998          47.890.123     +2.766.667
      ... (todos os 29 anos)
      Tempo: 0.0012s

[4/5] Filtro 3 — Peso Total por Região (kg)
      Região          Peso Total (kg)  % do Brasil
      --------------- ----------------------  ------------
      Centro-Oeste          432.109.876.543         38.1%
      ... (todas as 5 regiões)
      Tempo: 0.8100s

[5/5] Filtro 4 — Federal × Estadual × Municipal (Brasil)
      Inspeção        Total de Cabeças  % do Total
      ------------ ----------------------  ----------
      Federal              876.543.210       72.5%
      Estadual             234.567.890       19.4%
      Municipal             98.765.432        8.1%
      Tempo: 0.0010s

============================================================
   Resumo de Tempos
============================================================
   Leitura do arquivo :    42.30s
   Filtro 1           :    0.8321s
   Filtro 2           :    0.0012s
   Filtro 3           :    0.8100s
   Filtro 4           :    0.0010s
   TOTAL              :    44.05s
============================================================
```

---

## paralelizado.py

Roda **exatamente os mesmos 4 filtros do `serial.py`**, mas divide as linhas entre N threads. A cada rodada (2, 4, 6, 8 e 12 threads) os resultados completos são exibidos — iguais ao serial — seguidos do tempo gasto. Ao final, uma tabela compara o speedup entre as configurações.

### Como a paralelização funciona

O arquivo é lido uma única vez. As linhas em memória são divididas em **N fatias iguais** e cada thread recebe sua fatia, rodando os 4 filtros de forma independente:

```
21.951 linhas (abatidos) + 21.951 linhas (peso)
│
├── thread 0  →  worker(fatia 0)  →  resultados parciais [0]  ─┐
├── thread 1  →  worker(fatia 1)  →  resultados parciais [1]   │ merge
├── ...                                                         │ (soma os dicts)
└── thread N  →  worker(fatia N)  →  resultados parciais [N]  ─┘
                                           │
                              exibir_resultados(r1, r2, r3, r4)
                              (mesma saída do serial.py)
```

Cada thread escreve no **seu próprio índice** do array de resultados — sem `Lock`, sem condição de corrida. O merge acontece no thread principal depois que todas terminam.

### Saída esperada

A cada rodada de N threads o script exibe os filtros completos e o tempo:

```
==============================================================
   Rodada com 2 threads
==============================================================

  Filtro 1 — Abate por Estado
  Estado                    Total de Cabeças  Rank
  Mato Grosso                  1.234.567.890  #1
  São Paulo                      987.654.321  #2
  ... (todos os 27 estados)

  Filtro 2 — Evolução Anual (Brasil)
  1997          45.123.456             —
  1998          47.890.123     +2.766.667
  ... (todos os 29 anos)

  Filtro 3 — Peso Total por Região (kg)
  Centro-Oeste    432.109.876.543        38.1%
  ... (todas as 5 regiões)

  Filtro 4 — Federal × Estadual × Municipal
  Federal       876.543.210       72.5%
  ...

  Tempo de processamento (2 threads): 2.3800s

==============================================================
   Rodada com 4 threads
==============================================================
  ... (mesmos resultados, mais rápido)
  Tempo de processamento (4 threads): 1.4200s

... (repete para 6, 8, 12 threads)

==============================================================
   Tabela de Speedup
==============================================================
  Threads     Tempo (s)     Speedup
  --------  ------------  ----------
         2        2.3800       1.00x
         4        1.4200       1.68x
         6        1.1500       2.07x
         8        0.9800       2.43x
        12        0.8900       2.67x
==============================================================
```

### Por que o speedup não é linear?

Em Python, o **GIL (Global Interpreter Lock)** impede que múltiplas threads executem código Python ao mesmo tempo em paralelo real. O ganho existe, mas é limitado — especialmente em tarefas de CPU pura como parsing e soma de valores.

Para escala próxima de N×, a alternativa seria `multiprocessing` (processos separados, sem GIL compartilhado). O uso de `threading` aqui demonstra corretamente:

- Criação e gerenciamento de threads
- Divisão de trabalho por particionamento de dados
- Merge de resultados parciais sem condição de corrida
- Medição e comparação de desempenho entre configurações

---

## Conceitos de PDC Aplicados

| Conceito | Onde aparece |
|---|---|
| **Paralelismo de dados** | As linhas do CSV são divididas em N fatias iguais, cada thread processa a sua |
| **Ausência de condição de corrida** | Cada thread escreve no seu próprio índice do array — sem memória compartilhada durante o processamento |
| **Merge de resultados** | Após o `join()`, o thread principal soma os dicionários parciais de cada thread |
| **Thread pool manual** | Threads criadas com `threading.Thread`, iniciadas com `.start()` e sincronizadas com `.join()` |
| **Speedup** | Medido como `tempo_2_threads / tempo_N_threads` — exibido na tabela final |
| **Overhead de thread** | Visível quando N alto tem ganho marginal menor que o esperado (custo de criação e sincronização) |
# trabalho_materia_pdc_2bimestre
