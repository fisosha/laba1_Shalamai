# -*- coding: utf-8 -*-
# Будує рисунки для звіту: fig_speedup.png, fig_time.png, fig_arch.png
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
W, T, S, E = [], [], [], []
with open(os.path.join(HERE, "results.csv")) as f:
    for r in csv.DictReader(f):
        W.append(int(r["workers"])); T.append(float(r["time_s"]))
        S.append(float(r["speedup"])); E.append(float(r["efficiency"]))

# Рисунок: прискорення
fig, ax = plt.subplots(figsize=(6.2, 4.3))
ax.plot(W, W, "--", color="#9aa0a6", label="ідеальне S = k")
ax.plot(W, S, "o-", color="#1a73e8", lw=2, ms=7, label="виміряне (модель)")
for x, y in zip(W, S):
    ax.annotate("%.2f" % y, (x, y), textcoords="offset points", xytext=(7, -11),
                fontsize=9, color="#1a73e8")
ax.set_xlabel("Кількість воркерів k"); ax.set_ylabel("Прискорення S = T₁ / Tₖ")
ax.set_xticks(W); ax.grid(True, alpha=0.3); ax.legend()
ax.set_title("Прискорення паралельного алгоритму")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "fig_speedup.png"), dpi=140); plt.close(fig)

#  Рисунок: час
fig, ax = plt.subplots(figsize=(6.2, 4.3))
ax.plot(W, T, "s-", color="#188038", lw=2, ms=7)
for x, y in zip(W, T):
    ax.annotate("%.2f с" % y, (x, y), textcoords="offset points", xytext=(7, 7),
                fontsize=9, color="#188038")
ax.set_xlabel("Кількість воркерів k"); ax.set_ylabel("Час задачі, с")
ax.set_xticks(W); ax.grid(True, alpha=0.3)
ax.set_title("Час виконання задачі")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "fig_time.png"), dpi=140); plt.close(fig)

#  Рисунок: архітектура
fig, ax = plt.subplots(figsize=(8.2, 4.6)); ax.axis("off")
ax.set_xlim(0, 10); ax.set_ylim(0, 7)

def box(x, y, w, h, text, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.12",
                 fc=fc, ec="#5f6368", lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9)

def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                 mutation_scale=12, color="#5f6368", lw=1.1))

box(3.3, 5.3, 3.4, 1.1, "МАЙСТЕР · solve()\nділить c = 1..T на k блоків", "#e8f0fe")
workers = ["воркер 1\nc:[1, b₁)", "воркер 2\nc:[b₁, b₂)",
           "воркер 3\nc:[b₂, b₃)", "воркер k\nc:[.., T]"]
xs = [0.4, 2.9, 5.4, 7.9]
for x, w in zip(xs, workers):
    box(x, 2.7, 2.0, 1.2, "ВОРКЕР · mymap\n" + w, "#e6f4ea")
    arrow(5.0, 5.3, x + 1.0, 3.9)       # майстер -> воркер
    arrow(x + 1.0, 2.7, 5.0, 1.6)       # воркер -> майстер
box(3.3, 0.4, 3.4, 1.1, "МАЙСТЕР · myreduce()\nзбирає дільники → розклад N", "#e8f0fe")
ax.text(5.0, 4.6, "Pyro4 (асинхронно): N і межі блоку → ; список дільників ←",
        ha="center", fontsize=8, color="#5f6368", style="italic")
ax.set_title("Схема керуючого простору «ДЕРЕВО» (зірка): PARCS map-reduce", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "fig_arch.png"), dpi=140); plt.close(fig)

print("Збережено: fig_speedup.png, fig_time.png, fig_arch.png")