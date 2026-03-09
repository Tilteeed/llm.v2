# python_runtime

Роль для безопасной установки отдельного Python runtime на Ubuntu без изменения системного `python3`.

## Что делает роль

- при необходимости подключает `deadsnakes PPA`;
- устанавливает Python 3.11;
- при необходимости создает отдельный `venv`;
- при необходимости обновляет `pip`, `setuptools`, `wheel` внутри `venv`.

## Что роль НЕ делает

- не меняет `/usr/bin/python3`;
- не делает Python 3.11 системным Python по умолчанию;
- не ломает `apt` и системные утилиты Ubuntu.

## Когда использовать

- если нужен современный Python для LangChain / LangGraph;
- если хост работает на Ubuntu 20.04;
- если нельзя рисковать системным Python.

## Пример запуска

```bash
ansible-playbook site.yml --tags python_runtime -K