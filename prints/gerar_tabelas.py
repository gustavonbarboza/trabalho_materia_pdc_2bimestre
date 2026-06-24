"""
Gera imagens PNG das tabelas de resultados.
Execute com: python3 gerar_tabelas.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT = "."

DARK  = "#0D1B3E"
DARK2 = "#0F2248"
BLUE  = "#4A90D9"
WHITE = "#FFFFFF"
GRAY  = "#A8C4E8"
GREEN = "#2ECC71"
MINT  = "#4DFFA0"
BORDER = "#1E3A6E"

# ─────────────────────────────────────────────────────────────────────────────
# Tabela 1 — Escalando de 1 a 12 processos
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 4.2))
fig.patch.set_facecolor(DARK)
ax.set_facecolor(DARK)
ax.axis("off")

col_labels = ["CONFIGURAÇÃO", "PRÉ-SCAN (s)", "PROC. (s)", "TOTAL (s)", "SPEEDUP PROC.", "SPEEDUP TOTAL"]
rows = [
    ["1 processo",   "41.41", "14.53", "55.94", "ref (1.00×)", "ref (1.00×)"],
    ["2 processos",  "41.41",  "7.60", "49.01",      "1.91×",      "1.14×"],
    ["4 processos",  "41.41",  "4.58", "45.99",      "3.17×",      "1.22×"],
    ["8 processos",  "41.41",  "2.87", "44.29",      "5.06×",      "1.26×"],
    ["12 processos", "41.41",  "2.31", "43.73",      "6.29×",      "1.28×"],
]

col_widths = [0.22, 0.13, 0.11, 0.11, 0.15, 0.15]
x_starts = []
x = 0.01
for w in col_widths:
    x_starts.append(x)
    x += w

ROW_H = 0.14
HEADER_Y = 0.88
DATA_Y_START = 0.72

# Título
ax.text(0.5, 0.97, "Escalando de 1 a 12 processos",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=16, fontweight="bold", color=WHITE)

# Linha separadora abaixo do título
ax.plot([0.01, 0.99], [0.91, 0.91], color=BORDER, linewidth=1.2,
        transform=ax.transAxes, clip_on=False)

# Cabeçalhos
for i, (label, xs, w) in enumerate(zip(col_labels, x_starts, col_widths)):
    ha = "left" if i == 0 else "right"
    xpos = xs + 0.005 if i == 0 else xs + w - 0.005
    ax.text(xpos, HEADER_Y, label,
            transform=ax.transAxes, ha=ha, va="center",
            fontsize=8.5, fontweight="bold", color=GRAY,
            fontfamily="DejaVu Sans")

# Linha separadora abaixo do cabeçalho
ax.plot([0.01, 0.99], [0.84, 0.84], color=BORDER, linewidth=0.8,
        transform=ax.transAxes, clip_on=False)

# Linhas de dados
for r_idx, row in enumerate(rows):
    y = DATA_Y_START - r_idx * ROW_H
    # fundo alternado
    if r_idx % 2 == 1:
        rect = plt.Rectangle((0.01, y - ROW_H * 0.55), 0.98, ROW_H,
                              transform=ax.transAxes, color="#0A1830",
                              zorder=0, clip_on=False)
        ax.add_patch(rect)

    for i, (cell, xs, w) in enumerate(zip(row, x_starts, col_widths)):
        ha = "left" if i == 0 else "right"
        xpos = xs + 0.005 if i == 0 else xs + w - 0.005

        # cor especial para speedup na última linha
        if r_idx == 4 and i in (4, 5):
            color = MINT
        elif "ref" in cell:
            color = GRAY
        elif i in (4, 5) and "×" in cell:
            color = GREEN
        elif i == 0:
            color = WHITE
        else:
            color = GRAY

        fw = "bold" if i == 0 else "normal"
        ax.text(xpos, y, cell,
                transform=ax.transAxes, ha=ha, va="center",
                fontsize=10.5, color=color, fontweight=fw,
                fontfamily="DejaVu Sans")

    # linha divisória
    if r_idx < len(rows) - 1:
        ax.plot([0.01, 0.99], [y - ROW_H * 0.55, y - ROW_H * 0.55],
                color=BORDER, linewidth=0.5, transform=ax.transAxes, clip_on=False)

fig.tight_layout(pad=0.4)
fig.savefig(f"{OUT}/tabela_resultados.png", dpi=160, bbox_inches="tight",
            facecolor=DARK)
plt.close(fig)
print("tabela_resultados.png ✓")

# ─────────────────────────────────────────────────────────────────────────────
# Tabela 2 — Eficiência Paralela
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 3.8))
fig.patch.set_facecolor(DARK)
ax.set_facecolor(DARK)
ax.axis("off")

YEL = "#F39C12"
RED = "#E74C3C"

col_labels2 = ["PROCESSOS", "TEMPO (s)", "SPEEDUP", "EFICIÊNCIA", "INTERPRETAÇÃO"]
rows2 = [
    ["1",  "14.53", "1.00×", "100%", "base — referência"],
    ["2",   "7.60", "1.91×",  "96%", "quase perfeito — núcleos sobrando"],
    ["4",   "4.58", "3.17×",  "79%", "bom — concorrência por disco"],
    ["8",   "2.87", "5.06×",  "63%", "joelho da curva — hyperthreads"],
    ["12",  "2.31", "6.29×",  "52%", "retornos decrescentes"],
]
ef_colors = [GREEN, GREEN, YEL, "#E67E22", RED]

col_widths2 = [0.10, 0.11, 0.10, 0.11, 0.45]
x_starts2 = []
x = 0.02
for w in col_widths2:
    x_starts2.append(x)
    x += w

HEADER_Y2 = 0.88
DATA_Y2 = 0.72

ax.text(0.5, 0.97, "Eficiência Paralela — Fase de Processamento",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=14, fontweight="bold", color=WHITE)

ax.plot([0.02, 0.98], [0.91, 0.91], color=BORDER, linewidth=1.2,
        transform=ax.transAxes, clip_on=False)

for i, (label, xs, w) in enumerate(zip(col_labels2, x_starts2, col_widths2)):
    ha = "left" if i in (0, 4) else "right"
    xpos = xs + 0.005 if i == 0 else (xs + w - 0.005 if i != 4 else xs + 0.005)
    ax.text(xpos, HEADER_Y2, label,
            transform=ax.transAxes, ha=ha, va="center",
            fontsize=8.5, fontweight="bold", color=GRAY)

ax.plot([0.02, 0.98], [0.84, 0.84], color=BORDER, linewidth=0.8,
        transform=ax.transAxes, clip_on=False)

for r_idx, (row, ef_color) in enumerate(zip(rows2, ef_colors)):
    y = DATA_Y2 - r_idx * ROW_H
    if r_idx % 2 == 1:
        rect = plt.Rectangle((0.02, y - ROW_H * 0.55), 0.96, ROW_H,
                              transform=ax.transAxes, color="#0A1830",
                              zorder=0, clip_on=False)
        ax.add_patch(rect)

    for i, (cell, xs, w) in enumerate(zip(row, x_starts2, col_widths2)):
        if i == 3:
            color = ef_color
            fw = "bold"
        elif i == 0:
            color = WHITE
            fw = "bold"
        elif i == 4:
            color = GRAY
            fw = "normal"
        else:
            color = GRAY
            fw = "normal"

        ha = "left" if i in (0, 4) else "right"
        xpos = xs + 0.005 if i == 0 else (xs + w - 0.005 if i != 4 else xs + 0.005)
        ax.text(xpos, y, cell,
                transform=ax.transAxes, ha=ha, va="center",
                fontsize=10.5, color=color, fontweight=fw)

    if r_idx < len(rows2) - 1:
        ax.plot([0.02, 0.98], [y - ROW_H * 0.55, y - ROW_H * 0.55],
                color=BORDER, linewidth=0.5, transform=ax.transAxes, clip_on=False)

fig.tight_layout(pad=0.4)
fig.savefig(f"{OUT}/tabela_eficiencia.png", dpi=160, bbox_inches="tight",
            facecolor=DARK)
plt.close(fig)
print("tabela_eficiencia.png ✓")

print("\nTodas as tabelas geradas em:", OUT)
