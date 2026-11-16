import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

k = [1, 2, 4]
cloud_s = [1.00, 1.97, 3.65]
cloud_tpar = [79.027, 40.228, 21.724]
cloud_tseq = [78.883, 79.370, 79.220]
local_k = [1, 2, 4, 8]
local_s = [1.00, 2.04, 3.87, 7.44]

fig, ax = plt.subplots(figsize=(6.2, 4.3))
ax.plot(local_k, local_k, "--", color="#999999", label="Ідеальне (S = k)")
ax.plot(local_k, local_s, "s-", color="#4c78a8", label="Локальна емуляція")
ax.plot(k, cloud_s, "o-", color="#e45756", linewidth=2, label="Azure (реальний кластер)")
for x, y in zip(k, cloud_s):
    ax.annotate("%.2f" % y, (x, y), textcoords="offset points", xytext=(6, -12), fontsize=9, color="#e45756")
ax.set_xlabel("Кількість воркерів k")
ax.set_ylabel("Прискорення S = T_посл / T_пар")
ax.set_xticks(local_k)
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig("fig_cloud_speedup.png", dpi=160)
plt.close(fig)

fig, ax = plt.subplots(figsize=(6.2, 4.0))
x = range(len(k))
ax.bar([i - 0.2 for i in x], cloud_tseq, width=0.4, color="#bab0ac", label="T_посл")
ax.bar([i + 0.2 for i in x], cloud_tpar, width=0.4, color="#e45756", label="T_пар")
for i, t in enumerate(cloud_tpar):
    ax.text(i + 0.2, t + 1.5, "%.1f" % t, ha="center", fontsize=9)
ax.set_xticks(list(x))
ax.set_xticklabels(["k = %d" % v for v in k])
ax.set_ylabel("Час, с")
ax.legend()
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("fig_cloud_time.png", dpi=160)
plt.close(fig)
