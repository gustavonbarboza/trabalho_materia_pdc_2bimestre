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
      Mato Grosso               1.234.567.890 cabeças
      ...
      Tempo: 0.8321s
...
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

Mantém a mesma leitura serial (o gargalo de I/O de 2 GB é difícil de paralelizar sem aumentar a complexidade do código), mas **paraleliza o processamento dos filtros**.

### Como a paralelização funciona

Após a leitura, as linhas em memória são divididas em **N fatias iguais**. Para cada fatia, são criadas threads para os 4 filtros simultaneamente:

```
rows_abatidos (21.951 linhas)
│
├── thread 0 → filtro_abate_estado(fatia 0)  ─┐
├── thread 1 → filtro_abate_estado(fatia 1)   │ merge com Lock
├── ...                                        │
└── thread N → filtro_abate_estado(fatia N)  ─┘

(mesmo padrão para filtros 2, 3 e 4 em paralelo)
```

Cada thread computa um dicionário parcial e usa um `threading.Lock` para acumular o resultado final com segurança.

### Configurações de threads testadas

O script roda automaticamente para `N = 2, 4, 6, 8, 12` threads e exibe uma tabela de speedup:

```
=================================================================
   Threads     Tempo (s)      Speedup
   ------------------------------------
         1        4.2100        1.00x
         2        2.3800        1.77x
         4        1.4200        2.96x
         6        1.1500        3.66x
         8        0.9800        4.30x
        12        0.8900        4.73x
=================================================================
```

### Por que o speedup não é linear?

Em Python, o **GIL (Global Interpreter Lock)** impede que múltiplas threads executem bytecode Python ao mesmo tempo. Isso significa que o ganho com threads é real, mas limitado — especialmente em tarefas de CPU pura como parsing e soma de floats.

Para obter speedup linear (escala próxima de N×), a alternativa em Python seria usar `multiprocessing` (processos separados, sem GIL compartilhado). O uso de `threading` aqui demonstra corretamente:

- Criação e gerenciamento de threads
- Divisão de trabalho (particionamento de dados)
- Sincronização com `Lock` para evitar condição de corrida
- Medição e comparação de desempenho

---

## Conceitos de PDC Aplicados

| Conceito | Onde aparece |
|---|---|
| **Paralelismo de dados** | As linhas do CSV são divididas em N partes iguais entre as threads |
| **Condição de corrida** | Seria gerada se threads escrevessem em `resultado` sem controle |
| **Exclusão mútua (Lock)** | Cada filtro tem seu próprio `Lock` — threads acumulam o resultado parcial com segurança |
| **Thread pool manual** | Lista de threads criadas, iniciadas e sincronizadas com `join()` |
| **Speedup** | Medido como `tempo_1_thread / tempo_N_threads` |
| **Overhead de thread** | Visível quando N alto tem ganho marginal menor que o esperado |
# trabalho_materia_pdc_2bimestre
