# ubuntu_base_nvidia_host

## Назначение

Роль для базовой подготовки Ubuntu-хоста под LLM-инфраструктуру.

## Что делает

- проверяет, что ОС — Ubuntu;
- обновляет apt cache;
- при необходимости выполняет dist-upgrade;
- ставит базовые системные утилиты;
- ставит Python 3, pip и venv;
- проверяет наличие NVIDIA GPU в PCI;
- ставит host NVIDIA driver через `ubuntu-drivers autoinstall`;
- выполняет reboot после установки драйвера;
- проверяет работоспособность GPU через `nvidia-smi`;
- проверяет наличие `/proc/driver/nvidia/gpus`.

## Что не делает

- не ставит Docker;
- не ставит NVIDIA Container Toolkit;
- не запускает контейнеры;
- не устанавливает Ollama.

Это будет вынесено в отдельные роли.
