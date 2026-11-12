# -*- coding: utf-8 -*-
#
# PARCS-Python: факторизація натурального числа методом Полларда rho.
# Послідовний і паралельний алгоритми в одному файлі (як у прикладах курсу).
#
# Написано за шаблоном офіційного прикладу examples/scripts/prime_solution.py
# (клас Solver з методами solve / mymap / myreduce / read_input / write_output).
#
# Модель КП "зірка" (map-reduce): master (solve) роздає кожному воркеру свій блок
# констант c для полінома f(x) = x^2 + c (mod N). Кожен воркер незалежно запускає
# Полларда rho для своїх c і повертає знайдені нетривіальні дільники. Master (reduce)
# збирає дільники і відновлює повний канонічний розклад N на прості.
#
# Послідовний алгоритм = той самий фіксований обсяг роботи (T запусків rho) на одному
# воркері; паралельний = той самий обсяг, розділений між k воркерами. Це гарантує
# чесне порівняння часу (ідентичні операції) і відтворюваність (x0=2, множина c фіксовані).
#
# Код сумісний з Python 2.7 (образ hummer12007/parcs-node) і Python 3 (локальна перевірка).

try:
    from Pyro4 import expose
except ImportError:
    def expose(func):
        return func

import time


class Solver:
    def __init__(self, workers=None, input_file_name=None, output_file_name=None):
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name
        self.workers = workers
        print("Inited")

    # MASTER
    def solve(self):
        print("Job Started")
        print("Workers %d" % len(self.workers))

        if self.is_bench_input():
            return self.solve_bench()

        (n, trials, max_iter, mode) = self.read_input()
        print("N=%d trials=%d max_iter=%d mode=%s" % (n, trials, max_iter, mode))

        t_seq = t_par = None
        divisors = []

        if mode in ("seq", "both"):
            t_seq, divisors = self.run_sequential(n, trials, max_iter)
            print("Sequential: %.3f s" % t_seq)

        if mode in ("par", "both"):
            t_par, divisors = self.run_parallel(n, trials, max_iter)
            print("Parallel:   %.3f s" % t_par)

        self.write_output(n, trials, max_iter, divisors, t_seq, t_par)
        print("Job Finished")

    def run_sequential(self, n, trials, max_iter):
        # Весь обсяг (T запусків) на одному воркері - базова лінія для прискорення.
        t0 = time.time()
        res = Solver.unwrap(self.workers[0].mymap(str(n), "1", str(1 + trials), str(max_iter)))
        t = time.time() - t0
        divisors = sorted(set(int(d) for d in res[1:]))
        return t, divisors

    def run_parallel(self, n, trials, max_iter):
        # Розділяємо множину констант c=1..T на k рівних блоків за кількістю воркерів.
        w = len(self.workers)
        step = trials // w
        t0 = time.time()
        mapped = []
        for i in range(w):
            lo = 1 + i * step
            hi = 1 + trials if i == w - 1 else 1 + (i + 1) * step
            print("map worker %d: c in [%d, %d)" % (i, lo, hi))
            mapped.append(self.workers[i].mymap(str(n), str(lo), str(hi), str(max_iter)))
        divisors, worker_times = self.myreduce(mapped)
        t = time.time() - t0
        print("worker times: %s" % worker_times)
        return t, divisors

    # WORKER
    @staticmethod
    @expose
    def mymap(n_str, lo_str, hi_str, max_iter_str):
        t0 = time.time()
        n = int(n_str)
        lo = int(lo_str)
        hi = int(hi_str)
        max_iter = int(max_iter_str)
        found = []
        for c in range(lo, hi):
            d = Solver.pollard_rho(n, c, max_iter)
            if d is not None and 1 < d < n:
                found.append(str(d))
        # елемент 0 - час воркера (str), далі - знайдені дільники (str)
        return ["%.4f" % (time.time() - t0)] + found

    @staticmethod
    @expose
    def myreduce(mapped):
        print("reduce")
        divisors = set()
        times = []
        for item in mapped:
            part = Solver.unwrap(item)       # .value у Pyro4 / сам результат локально
            times.append(float(part[0]))
            for d in part[1:]:
                divisors.add(int(d))
        print("reduce done")
        return sorted(divisors), times

    @staticmethod
    def unwrap(item):
        # Pyro4 async повертає FutureResult з полем .value; локальний виклик - сам результат.
        return item.value if hasattr(item, "value") else item

    # АЛГОРИТМ
    @staticmethod
    @expose
    def pollard_rho(n, c, max_iter):
        # Класичний Полларда rho з детекцією циклу за Флойдом (черепаха/заєць).
        # f(x) = (x*x + c) mod n, x0 = 2 (фіксовано -> повна відтворюваність).
        if n % 2 == 0:
            return 2
        x = 2
        y = 2
        d = 1
        i = 0
        while d == 1 and i < max_iter:
            x = (x * x + c) % n            # черепаха: один крок
            y = (y * y + c) % n            # заєць: два кроки
            y = (y * y + c) % n
            diff = x - y
            if diff < 0:
                diff = -diff
            d = Solver.gcd(diff, n)
            i += 1
        if 1 < d < n:
            return d
        return None

    @staticmethod
    @expose
    def gcd(a, b):
        while b != 0:
            a, b = b, a % b
        return a

    @staticmethod
    @expose
    def is_probable_prime(n):
        # Детермінований тест Міллера-Рабіна (надійний для n < 3.3 * 10^24).
        if n < 2:
            return False
        for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
            if n % p == 0:
                return n == p
        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            composite = True
            for _ in range(s - 1):
                x = (x * x) % n
                if x == n - 1:
                    composite = False
                    break
            if composite:
                return False
        return True

    @staticmethod
    def full_factorization(n, divisors):
        # Зі знайдених дільників будуємо повний розклад на прості (і для p*q, і для кількох множників).
        primes = []
        stack = [n]
        cand = sorted(set(divisors))
        while stack:
            m = stack.pop()
            if m == 1:
                continue
            if Solver.is_probable_prime(m):
                primes.append(m)
                continue
            split = None
            for d in cand:
                if 1 < d < m and m % d == 0:
                    split = d
                    break
            if split is None:
                split = Solver.pollard_rho(m, 1, 10 ** 7)
            if split is None or split in (1, m):
                primes.append(m)
            else:
                stack.append(split)
                stack.append(m // split)
        return sorted(primes)

    # БЕНЧМАРК
    def is_bench_input(self):
        f = open(self.input_file_name, "r")
        first = f.readline().strip().lower()
        f.close()
        return first == "bench"

    def read_bench_input(self):
        # Формат: рядок1 = "bench"; рядок2 = K (повтори); далі - числа N (по одному на рядок).
        f = open(self.input_file_name, "r")
        lines = [ln.strip() for ln in f.readlines() if ln.strip()]
        f.close()
        k = int(lines[1])
        numbers = [int(x) for x in lines[2:]]
        return k, numbers

    def solve_bench(self):
        k, numbers = self.read_bench_input()
        trials, max_iter = 256, 100000
        f = open(self.output_file_name, "w")
        f.write("Benchmark: workers=%d, repeats=%d\n\n" % (len(self.workers), k))
        f.write("%-24s %10s %10s %7s\n" % ("N", "T_seq,s", "T_par,s", "S"))
        for n in numbers:
            seqs, pars = [], []
            for _ in range(k):
                ts, _ = self.run_sequential(n, trials, max_iter)
                tp, _ = self.run_parallel(n, trials, max_iter)
                seqs.append(ts)
                pars.append(tp)
            avg_seq = sum(seqs) / len(seqs)
            avg_par = sum(pars) / len(pars)
            s = avg_seq / avg_par if avg_par > 0 else 0
            f.write("%-24d %10.3f %10.3f %7.2f\n" % (n, avg_seq, avg_par, s))
        f.close()
        print("Bench finished")

    # I/O
    def read_input(self):
        # Формат (3-4 рядки):
        #   N         - число, яке факторизуємо
        #   trials    - кількість незалежних запусків rho (різних c)
        #   max_iter  - обмеження ітерацій на один запуск
        #   mode      - both | seq | par  (необов'язково, за замовчуванням both)
        f = open(self.input_file_name, "r")
        lines = [ln.strip() for ln in f.readlines() if ln.strip()]
        f.close()
        n = int(lines[0])
        trials = int(lines[1]) if len(lines) > 1 else 256
        max_iter = int(lines[2]) if len(lines) > 2 else 100000
        mode = lines[3].lower() if len(lines) > 3 else "both"
        return n, trials, max_iter, mode

    def write_output(self, n, trials, max_iter, divisors, t_seq, t_par):
        primes = Solver.full_factorization(n, divisors)
        product = 1
        for p in primes:
            product *= p
        f = open(self.output_file_name, "w")
        f.write("N = %d\n" % n)
        f.write("Параметри: trials=%d, max_iter=%d\n" % (trials, max_iter))
        f.write("Нетривіальні дільники (від воркерів): %s\n"
                % ", ".join(str(d) for d in divisors))
        f.write("Розклад на прості: %s\n" % " * ".join(str(p) for p in primes))
        f.write("Перевірка добутку: %s\n" % ("OK" if product == n else "ПОМИЛКА"))
        if t_seq is not None:
            f.write("T_посл = %.3f с\n" % t_seq)
        if t_par is not None:
            f.write("T_пар  = %.3f с (воркерів: %d)\n" % (t_par, len(self.workers)))
        if t_seq is not None and t_par is not None and t_par > 0:
            s = t_seq / t_par
            f.write("Прискорення S = %.2f, Ефективність E = %.2f\n"
                    % (s, s / len(self.workers)))
        f.close()
        print("output done")