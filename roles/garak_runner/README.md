# garak_runner

## Назначение

Роль для подготовки окружения Garak на Ubuntu-хосте в отдельном Python virtual environment.

## Что делает

- проверяет наличие python3 и python3-venv;
- проверяет доступность Ollama API;
- создает каталоги под Garak;
- создает отдельный Python virtual environment;
- обновляет pip/setuptools/wheel;
- устанавливает пакет `garak`;
- проверяет доступность CLI `garak`;
- создает helper-скрипт для запуска Garak против Ollama.

## Что не делает

- не запускает полноценный scan автоматически;
- не управляет пользователями;
- не разворачивает Ollama.

Это выполняется другими ролями.