# Запуск PARCS-Python у Microsoft Azure

Підписка: Azure for Students (GitHub Student Developer Pack).
Кластер: `master` (Standard_B1s, публічна IP, веб-інтерфейс на порту 8080)
і 4 воркери (Standard_A1_v2, лише внутрішня IP, вихід в Інтернет через NAT-шлюз).
Регіон: `denmarkeast` (студентська підписка дозволяє лише кілька регіонів).
На кожній машині працює Docker-образ `hummer12007/parcs-node`.

## Розгортання

В Azure Cloud Shell (Bash), з кореня репозиторію:

    bash cloud/azure_deploy.sh

Наприкінці скрипт виводить адресу веб-інтерфейсу `http://IP:8080`.
Через 3–5 хвилин на вкладці Nodes з'являються 4 воркери.

## Заміри

1. На вкладці Nodes залишити увімкненими k воркерів (Disable / Enable), воркер #0 — завжди.
2. На вкладці Add Job завантажити `factorization.py` і `inputs/05_semiprime_1e18.txt`.
3. На вкладці Jobs відкрити Output: там T_посл, T_пар, прискорення S і ефективність E.

Результати запусків для k = 1, 2, 4 — у папці `cloud_results/`.

## Видалення

    bash cloud/azure_cleanup.sh
