# -*- coding: utf-8 -*-
#
# Локальний запуск / емулятор PARCS для factorization.py.
#
#   python3 local_run.py --test              # самоперевірка факторизації на всіх inputs/
#   python3 local_run.py inputs/05_...txt     # заміри прискорення k=1,2,4,8 + results.csv
#   python3 local_run.py --cross inputs/05_...txt  # реальний крос-чек на процесах (k=2)
#
# Модель: кожен воркер PARCS - окрема ВМ (1 vCPU). Час кожного блоку міряємо
# незалежно на одному ядрі, а час розподіленого запуску = max серед блоків
# (воркери працюють одночасно на різних машинах). Реальний крос-чек на 2 ядрах
# підтверджує модель для k=2.
#
import sys
import os
import csv
import time
import glob
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("factorization", os.path.join(HERE, "factorization.py"))
fac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fac)
Solver = fac.Solver

REPEATS = 3
WORKER_COUNTS = [1, 2, 4, 8]


def read_input(path):
    with open(path) as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    return int(lines[0]), int(lines[1]), int(lines[2])


def self_test():
    print("ПЕРЕВІРКА КОРЕКТНОСТІ ФАКТОРИЗАЦІЇ")
    ok_all = True
    for path in sorted(glob.glob(os.path.join(HERE, "inputs", "*.txt"))):
        n, trials, max_iter = read_input(path)
        res = Solver.mymap(str(n), "1", str(1 + trials), str(max_iter))
        divisors = sorted(set(int(d) for d in res[1:]))
        primes = Solver.full_factorization(n, divisors)
        prod = 1
        for p in primes:
            prod *= p
        ok = (prod == n)
        ok_all = ok_all and ok
        print("%-28s N=%-22d -> %s  [%s]"
              % (os.path.basename(path), n,
                 " * ".join(str(p) for p in primes), "OK" if ok else "FAIL"))
    print("results match:", "YES" if ok_all else "NO")
    return ok_all


def block_bounds(trials, w):
    step = trials // w
    out = []
    for i in range(w):
        lo = 1 + i * step
        hi = 1 + trials if i == w - 1 else 1 + (i + 1) * step
        out.append((lo, hi))
    return out


def time_block(n, lo, hi, max_iter):
    best = None
    for _ in range(REPEATS):
        t0 = time.time()
        Solver.mymap(str(n), str(lo), str(hi), str(max_iter))
        dt = time.time() - t0
        best = dt if best is None else min(best, dt)
    return best


def scaling(path):
    n, trials, max_iter = read_input(path)
    print("ЗАМІРИ (модель розподіленого запуску)")
    print("N=%d, trials=%d, max_iter=%d, repeats=%d" % (n, trials, max_iter, REPEATS))
    rows = []
    t1 = None
    for w in WORKER_COUNTS:
        blocks = [time_block(n, lo, hi, max_iter) for (lo, hi) in block_bounds(trials, w)]
        t_wall = max(blocks)
        t_sum = sum(blocks)
        if w == 1:
            t1 = t_wall
        s = t1 / t_wall
        e = s / w
        # метрика Карпа-Флатта (для w>1)
        kf = ((1.0 / s) - (1.0 / w)) / (1.0 - (1.0 / w)) if w > 1 else None
        rows.append((w, t_wall, t_sum, s, e, kf))
        print("W=%d  T=%6.2fs  Tsum=%6.2fs  S=%4.2f  E=%4.2f  Karp-Flatt=%s"
              % (w, t_wall, t_sum, s, e, "%.3f" % kf if kf is not None else "-"))
    with open(os.path.join(HERE, "results.csv"), "w") as f:
        wr = csv.writer(f)
        wr.writerow(["workers", "time_s", "total_work_s", "speedup", "efficiency", "karp_flatt"])
        for r in rows:
            wr.writerow(["%d" % r[0], "%.2f" % r[1], "%.2f" % r[2], "%.2f" % r[3],
                         "%.2f" % r[4], "" if r[5] is None else "%.3f" % r[5]])
    print("-> results.csv")
    return rows


def _block_worker(args):
    n, lo, hi, max_iter = args
    t0 = time.time()
    Solver.mymap(str(n), str(lo), str(hi), str(max_iter))
    return time.time() - t0


def cross_check(path):
    # Реальний запуск на процесах (скільки ядер є) для k=2 - перевірка моделі.
    import multiprocessing as mp
    n, trials, max_iter = read_input(path)
    print("РЕАЛЬНИЙ КРОС-ЧЕК НА ПРОЦЕСАХ (k=2)")
    # послідовно
    t0 = time.time()
    _block_worker((n, 1, 1 + trials, max_iter))
    t_seq = time.time() - t0
    # паралельно на 2 процесах
    bounds = block_bounds(trials, 2)
    args = [(n, lo, hi, max_iter) for (lo, hi) in bounds]
    pool = mp.Pool(2)
    t0 = time.time()
    pool.map(_block_worker, args)
    t_par = time.time() - t0
    pool.close(); pool.join()
    print("T_seq=%.2fs  T_par(2 proc)=%.2fs  S=%.2f (реальний замір на %d ядрах)"
          % (t_seq, t_par, t_seq / t_par, mp.cpu_count()))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or "--test" in args:
        self_test()
    if args and args[0] == "--cross":
        cross_check(args[1])
    elif args and not args[0].startswith("--"):
        scaling(args[0])