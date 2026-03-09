# docker_engine

## Назначение

Роль для установки Docker Engine на Ubuntu из официального Docker repository.

## Что делает

- проверяет, что ОС — Ubuntu;
- проверяет базовую сетевую доступность Docker repo;
- ставит пакеты-предпосылки;
- удаляет старые конфликтующие Docker-пакеты;
- добавляет официальный GPG-ключ Docker;
- добавляет официальный apt repository Docker;
- устанавливает Docker Engine и docker compose plugin;
- включает и запускает сервис Docker;
- создает/проверяет группу `docker`;
- добавляет существующих пользователей в группу `docker`;
- проверяет `docker version` и `docker info`;
- опционально запускает `hello-world`.

## Что не делает

- не настраивает GPU для контейнеров;
- не устанавливает NVIDIA Container Toolkit;
- не запускает Ollama.

Это будет в следующих ролях.