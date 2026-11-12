# -*- coding: utf-8 -*-

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)        # щоб імпорти local_run / charts працювали

import local_run                # noqa: E402


def main():
    main_input = os.path.join(HERE, "inputs", "05_semiprime_1e18.txt")

    print("\nКРОК 1: ПЕРЕВІРКА КОРЕКТНОСТІ")
    local_run.self_test()

    print("\nКРОК 2: ЗАМІРИ ПРИСКОРЕННЯ (k=1,2,4,8)")
    print("(займе ~1-2 хв, рахує чесно)\n")
    local_run.scaling(main_input)

    print("\nКРОК 3: РЕАЛЬНИЙ ЗАПУСК НА ПРОЦЕСАХ")
    try:
        local_run.cross_check(main_input)
    except Exception as e:
        print("(крок необов'язковий, пропущено: %s)" % e)

    print("\nКРОК 4: ГРАФІКИ")
    try:
        import charts  # noqa: F401
        print("Готово: fig_speedup.png, fig_time.png, fig_arch.png")
    except Exception as e:
        print("Графіки пропущено (немає matplotlib?): %s" % e)
        print("Встанови: pip3 install matplotlib")

    print("\nГОТОВО. Результати - у results.csv, графіки - у fig_*.png")


if __name__ == "__main__":
    main()
