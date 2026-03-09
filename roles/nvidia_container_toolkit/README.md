# nvidia_container_toolkit

## Назначение

Роль для настройки поддержки NVIDIA GPU внутри Docker-контейнеров на Ubuntu.

## Что делает

- проверяет, что ОС — Ubuntu;
- проверяет, что host NVIDIA driver уже установлен и работает;
- проверяет, что Docker уже установлен;
- проверяет сетевую доступность NVIDIA repository;
- ставит пакеты-предпосылки;
- подключает официальный репозиторий NVIDIA Container Toolkit;
- устанавливает `nvidia-container-toolkit`;
- выполняет `nvidia-ctk runtime configure --runtime=docker`;
- перезапускает Docker;
- проверяет доступность GPU внутри контейнера через `docker run --gpus all ... nvidia-smi`.

## Что не делает

- не запускает Ollama;
- не управляет моделями;
- не разворачивает другие LLM-сервисы.

Это будет вынесено в следующие роли.