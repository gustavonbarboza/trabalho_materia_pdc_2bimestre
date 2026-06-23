"""
Gera os graficos de desempenho do trabalho paralelizado.
Execute com: python3 gerar_graficos.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT = "."

# ── Dados ─────────────────────────────────────────────────────────────────────
processos   = [1, 2, 4, 8, 12]
tempo_proc  = [14.53, 7.60, 4.58, 2.87, 2.31]
tempo_total = [55.94, 49.01, 45.99, 44.29, 43.73]
speedup_tot = [5.96, 6.80, 7.25, 7.53, 7.63]
speedup_proc= [1.00, 1.91, 3.17, 5.06, 6.29]
eficiencia  = [100, 96, 79, 63, 52]

SERIAL_TOTAL = 333.51
SERIAL_PROC  = 198.17
PRESCAN      = 41.41

DARK  = "#0D1B3E"
MINT  = "#4DFFA0"
BLUE  = "#4A90D9"
WHITE = "#FFFFFF"
GRAY  = "#64748B"
RED   = "#E74C3C"
YEL   = "#F39C12"
GREEN = "#2ECC71"

BAR_COLORS = [BLUE, GREEN, GREEN, YEL, RED]

STYLE = {
    "figure.facecolor": DARK,
    "axes.facecolor":   "#0F2248",
    "axes.edgecolor":   "#1E3A6E",
    "axes.labelcolor":  "#A8C4E8",
    "axes.titlecolor":  WHITE,
    "xtick.color":      "#A8C4E8",
    "ytick.color":      "#A8C4E8",
    "text.color":       WHITE,
    "grid.color":       "#1E3A6E",
    "grid.linestyle":   "--",
    "grid.alpha":       0.6,
    "font.family":      "DejaVu Sans",
}

plt.rcParams.update(STYLE)

# ─────────────────────────────────────────────────────────────────────────────
# Gráfico 1 — Speedup Total vs. Serial
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(processos, speedup_tot, color=MINT, marker="o", linewidth=2.5,
        markersize=8, markerfacecolor=DARK, markeredgewidth=2, zorder=3)
ax.axhline(8.05, color=YEL, linewidth=1.2, linestyle="--", alpha=0.7)
ax.text(11.5, 8.12, "teto de Amdahl\n8.05×", color=YEL, fontsize=9, ha="right")

for x, y in zip(processos, speedup_tot):
    ax.annotate(f"{y:.2f}×", (x, y), textcoords="offset points",
                xytext=(0, 10), ha="center", fontsize=10,
                color=MINT, fontweight="bold")

ax.fill_between(processos, speedup_tot, alpha=0.08, color=MINT)
ax.set_xlabel("Número de processos", fontsize=11)
ax.set_ylabel("Speedup vs. execução serial", fontsize=11)
ax.set_title("Speedup Total — Paralelo vs. Serial (333.51s)", fontsize=13, fontweight="bold", pad=14)
ax.set_xticks(processos)
ax.set_yticks([1, 2, 3, 4, 5, 6, 7, 7.63, 8.05])
ax.set_yticklabels(["1×", "2×", "3×", "4×", "5×", "6×", "7×", "7.63×", "8.05×"])
ax.set_ylim(4.5, 9.0)
ax.grid(True, axis="y")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(f"{OUT}/speedup_total.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("speedup_total.png ✓")

# ─────────────────────────────────────────────────────────────────────────────
# Gráfico 2 — Tempo de Processamento Paralelo (barras horizontais)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 4.5))
labels = [f"{p} proc" for p in processos]
bars = ax.barh(labels, tempo_proc, color=BAR_COLORS, height=0.55,
               edgecolor="none", zorder=3)

for bar, t, sp in zip(bars, tempo_proc, speedup_proc):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
            f"  {t:.2f}s  ({sp:.2f}×)",
            va="center", ha="left", fontsize=10.5, color=WHITE)

ax.set_xlabel("Tempo de processamento (s)", fontsize=11)
ax.set_title("Tempo de Processamento Paralelo por Nº de Processos\n(referência: 1 processo = 14.53s)", fontsize=12, fontweight="bold", pad=12)
ax.set_xlim(0, 22)
ax.invert_yaxis()
ax.grid(True, axis="x")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(f"{OUT}/tempo_processamento.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("tempo_processamento.png ✓")

# ─────────────────────────────────────────────────────────────────────────────
# Gráfico 3 — Eficiência (%)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
ef_colors = [GREEN if e >= 90 else (YEL if e >= 70 else RED) for e in eficiencia]
bars = ax.bar(processos, eficiencia, color=ef_colors, width=1.8,
              edgecolor="none", zorder=3)
ax.axhline(100, color=WHITE, linewidth=1.0, linestyle="--", alpha=0.35)
ax.text(12.2, 101, "100% (ideal)", color=WHITE, fontsize=9, alpha=0.5)

for bar, e in zip(bars, eficiencia):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
            f"{e}%", ha="center", va="bottom", fontsize=11,
            fontweight="bold",
            color=GREEN if e >= 90 else (YEL if e >= 70 else RED))

ax.set_xlabel("Número de processos", fontsize=11)
ax.set_ylabel("Eficiência (%)", fontsize=11)
ax.set_title("Eficiência Paralela\n(Eficiência = Speedup ÷ Nº Processos × 100%)", fontsize=12, fontweight="bold", pad=12)
ax.set_xticks(processos)
ax.set_ylim(0, 115)
ax.grid(True, axis="y")
ax.spines[["top", "right"]].set_visible(False)

legend = [
    mpatches.Patch(color=GREEN, label="≥ 90% — ótimo"),
    mpatches.Patch(color=YEL,   label="70–89% — bom"),
    mpatches.Patch(color=RED,   label="< 70% — retornos decrescentes"),
]
ax.legend(handles=legend, loc="upper right", fontsize=9,
          facecolor="#0F2248", edgecolor="#1E3A6E", labelcolor=WHITE)
fig.tight_layout()
fig.savefig(f"{OUT}/eficiencia.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("eficiencia.png ✓")

# ─────────────────────────────────────────────────────────────────────────────
# Gráfico 4 — Composição do Tempo Total (pré-scan + processamento)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))

configs  = ["Serial", "1 proc", "2 proc", "4 proc", "8 proc", "12 proc"]
prescan  = [135.12,   41.41,  41.41,  41.41,  41.41,  41.41]
proc_t   = [198.17,   14.53,   7.60,   4.58,   2.87,   2.31]
x = np.arange(len(configs))
w = 0.5

b1 = ax.bar(x, prescan, w, label="Leitura / Pré-scan", color=BLUE, zorder=3)
b2 = ax.bar(x, proc_t,  w, bottom=prescan, label="Processamento paralelo", color=MINT, zorder=3)

# Total labels on top
for xi, ps, pt in zip(x, prescan, proc_t):
    total = ps + pt
    ax.text(xi, total + 4, f"{total:.1f}s", ha="center", va="bottom",
            fontsize=9, color=WHITE, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(configs)
ax.set_ylabel("Tempo (s)", fontsize=11)
ax.set_title("Composição do Tempo Total por Configuração\n(leitura/pré-scan + processamento)", fontsize=12, fontweight="bold", pad=12)
ax.legend(loc="upper right", fontsize=10, facecolor="#0F2248",
          edgecolor="#1E3A6E", labelcolor=WHITE)
ax.set_ylim(0, 390)
ax.grid(True, axis="y")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(f"{OUT}/composicao_tempo.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("composicao_tempo.png ✓")

# ─────────────────────────────────────────────────────────────────────────────
# Gráfico 5 — Speedup do Processamento (isolado, sem pré-scan)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
ideal = [1.0, 2.0, 4.0, 8.0, 12.0]
ax.plot(processos, ideal, color=WHITE, linewidth=1.2, linestyle="--",
        alpha=0.3, label="Ideal (linear)", zorder=2)
ax.plot(processos, speedup_proc, color=MINT, marker="o", linewidth=2.5,
        markersize=9, markerfacecolor=DARK, markeredgewidth=2.5,
        label="Speedup real", zorder=3)

ax.fill_between(processos, speedup_proc, alpha=0.08, color=MINT)

for x_, y_ in zip(processos, speedup_proc):
    ax.annotate(f"{y_:.2f}×", (x_, y_), textcoords="offset points",
                xytext=(0, 10), ha="center", fontsize=10,
                color=MINT, fontweight="bold")

ax.set_xlabel("Número de processos", fontsize=11)
ax.set_ylabel("Speedup (base: 1 processo = 14.53s)", fontsize=11)
ax.set_title("Speedup do Processamento Paralelo\n(isolado — sem contabilizar o pré-scan)", fontsize=12, fontweight="bold", pad=12)
ax.set_xticks(processos)
ax.legend(loc="upper left", fontsize=10, facecolor="#0F2248",
          edgecolor="#1E3A6E", labelcolor=WHITE)
ax.set_ylim(0, 13)
ax.grid(True, axis="y")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(f"{OUT}/speedup_processamento.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("speedup_processamento.png ✓")

print("\nTodos os gráficos gerados em:", OUT)
