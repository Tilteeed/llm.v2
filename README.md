# Что это за проект?

`llm.v2` — это Ansible-проект для подготовки Ubuntu-хоста под LLM workloads и связанные сервисы.

Проект запускается через основной playbook `site.yml` и работает с группой хостов `llm_nodes`.

Хост собирается из набора ролей: 
- базовая настройка Ubuntu
- GPU host setup
- Docker
- NVIDIA Container Toolkit
- Отдельный Python runtime
- Ollama
- Загрузка моделей
- Monitoring stack
- Garak
- LangChain
- Platform users.

В inventory уже предусмотрены несколько сценариев: 
- `wsl2_gpu`
- `cloud_gpu_ready`
- `cloud_gpu_install`
- `cpu_only`

По сути, это единая инфраструктурная точка входа для развёртывания и приведения разных LLM-хостов к предсказуемому состоянию через роли и переменные Ansible.

---

# Что разворачивает проект

- Базовую подготовку Ubuntu-хоста
  - обновление apt cache;
  - установка базовых системных пакетов;
  - установка Python-инструментов, которые нужны проекту для дальнейших ролей.
 
- GPU-стек для NVIDIA-хостов
  - проверку доступности GPU;
  - при необходимости установку NVIDIA driver на обычной Ubuntu VM;
  - пост-проверки через nvidia-smi;
  - отдельный WSL2-совместимый режим, где Linux host driver внутри Ubuntu не ставится.

- Docker-инфраструктуру
  - подключение официального Docker repository;
  - установку Docker Engine и связанных пакетов;
  - запуск и включение Docker service;
  - подготовку хоста к запуску контейнерных сервисов.

- NVIDIA Container Toolkit
  - установку nvidia-container-toolkit;
  - настройку Docker runtime для GPU-контейнеров;
  - проверку того, что контейнеры могут видеть GPU.

- Отдельный Python runtime
  - сборку и установку отдельного Python из исходников;
  - установку в отдельный prefix;
  - работу без замены системного /usr/bin/python3;
  - при необходимости создание отдельного venv.

- Ollama в контейнере
  - создание каталогов и Docker network;
  - генерацию docker compose конфигурации;
  - запуск контейнера Ollama;
  - проверку доступности Ollama API после запуска.

- Модели для Ollama
  - проверку уже загруженных моделей;
  - подтягивание недостающих моделей через ollama pull;
  - синхронизацию списка моделей, который задан переменными проекта.

- Monitoring stack
  - развёртывание мониторинга через Docker Compose;
  - конфигурацию Prometheus;
  - запуск Grafana;
  - подготовку provisioning для datasource и dashboards.

- Garak
  - отдельное Python virtual environment;
  - установку пакета garak;
  - smoke-check CLI;
  - helper-скрипт для запуска проверок против Ollama endpoint.

- LangChain runtime
  - отдельный venv под LangChain;
  - установку пакетов langchain, langchain_community, langgraph и связанных зависимостей;
  - проверку импорта установленного Python-стека.

- Platform users
  - создание пользователей;
  - добавление их в группы sudo и docker;
  - при необходимости создание общей группы и общего каталога для командной работы.

- Все это собирается единым playbook site.yml
  - проект запускает роли последовательно для группы llm_nodes;
  - состав развёртывания зависит от выбранного сценария хоста: `wsl2_gpu`, `cloud_gpu_ready`, `cloud_gpu_install` или `cpu_only`.

---

# Поддерживаемые сценарии

Проект сейчас поддерживает 4 сценария хостов:

- `wsl2_gpu`
- `cloud_gpu_ready`
- `cloud_gpu_install`
- `cpu_only`

Все они входят в общую группу llm_nodes, на которую и запускается основной site.yml.

## Сценарий `wsl2_gpu`:

- Cценарий для WSL2 + GPU;
- GPU-стек включен;
- NVIDIA host driver не устанавливается;
- Docker управляется проектом;
- NVIDIA Container Toolkit управляется проектом;
- Ollama запускается с GPU;
- Cadvisor в monitoring stack отключен.

## Сценарий `cloud_gpu_ready`:

- Cценарий для облачного GPU-хоста, где основная GPU/Docker-база уже готова;
- GPU-стек включен;
- Docker не устанавливается проектом;
- NVIDIA host driver не устанавливается;
- NVIDIA Container Toolkit не настраивается проектом;
- Ollama запускается с GPU;
- Cadvisor в monitoring stack включен.

## Сценарий `cloud_gpu_install`:

- Сценарий для облачного GPU-хоста, который нужно подготовить почти с нуля;
- GPU-стек включен;
- Docker устанавливается и настраивается проектом;
- NVIDIA host driver устанавливается проектом;
- NVIDIA Container Toolkit устанавливается и настраивается проектом;
- Ollama запускается с GPU;
- Сadvisor в monitoring stack включен(Не тестировался).

## Сценарий `cpu_only`:

- Сценарий для хоста без GPU;
- GPU-стек отключен;
- NVIDIA driver и NVIDIA Container Toolkit не используются;
- Docker управляется проектом;
- Ollama запускается без GPU, в CPU-режиме;
- Сadvisor в monitoring stack отключен.

---

# Архитектура проекта

Проект построен по классической схеме Ansible orchestration:
- `ansible.cfg` задает базовую конфигурацию запуска;
- `inventory/hosts.ini` определяет хосты и сценарные группы;
- `site.yml` выступает центральной точкой входа;
- `group_vars/` хранит общие и сценарные переменные;
- `roles/` содержит прикладную логику по отдельным компонентам.

Логика работы идет сверху вниз:
  1. Ansible берет inventory из `inventory/hosts.ini`;
  2. playbook запускается на группе `llm_nodes`;
  3. в `pre_tasks` выбирается Python strategy и вычисляются управляющие флаги;
  4. дальше роли подключаются последовательно, а часть из них включается или пропускается через `when`.

По слоям проект можно читать так:
- слой хоста — `ubuntu_base`, `ubuntu_base_nvidia_host`, `docker_engine`, `nvidia_container_toolkit`, `python_runtime`;
- слой сервисов — `ollama_container`, `ollama_pull_models`, `monitoring_stack`;
- слой инструментов и доступа — `garak_runner`, `langchain_runtime`, `platform_users`.

Конфигурация сделана по принципу:
- в `group_vars/all.yml` лежат общие дефолты проекта;
- в `group_vars/*.yml` лежат переопределения под конкретный сценарий;
- профили меняют только то, что реально отличается между `wsl2_gpu`, `cloud_gpu_ready`, `cloud_gpu_install` и `cpu_only`.

---

# Структура репозитория

```
llm.v2/
├── group_vars/
│   ├── all.yml
│   ├── cloud_gpu_install.yml
│   ├── cloud_gpu_ready.yml
│   ├── cpu_only.yml
│   └── wsl2_gpu.yml
├── inventory/
│   └── hosts.ini
├── roles/
│   ├── docker_engine/tasks/main.yml
│   ├── garak_runner/tasks/main.yml
│   ├── langchain_runtime/tasks/main.yml
│   ├── monitoring_stack/tasks/main.yml
│   ├── nvidia_container_toolkit/tasks/main.yml
│   ├── ollama_container/tasks/main.yml
│   ├── ollama_pull_models/tasks/main.yml
│   ├── platform_users/tasks/main.yml
│   ├── python_runtime/tasks/main.yml
│   ├── ubuntu_base/tasks/main.yml
│   └── ubuntu_base_nvidia_host/tasks/main.yml
├── README.md
├── ansible.cfg
└── site.yml
```

Что за что отвечает:
- group_vars/ — общие и сценарные переменные проекта;
- inventory/ — inventory с хостами и группами;
- roles/ — вся основная логика развёртывания по компонентам;
- ansible.cfg — базовая конфигурация Ansible для этого репозитория;
- site.yml — главный playbook, который запускает роли проекта;
- README.md — документация проекта.

По смыслу репозиторий разделен на 3 основных слоя:
- inventory — где и на какие сценарии запускать;
- variables — какие параметры использовать;
- roles — что именно устанавливать и настраивать.

---

# Выбор сценария

Проект использует inventory-файл `inventory/hosts.ini`, а `ansible.cfg` уже настроен так, чтобы Ansible брал inventory именно оттуда.
В hosts.ini есть общая группа `llm_nodes:children`, в которую включены 4 сценарные группы:
- wsl2_gpu
- cloud_gpu_ready
- cloud_gpu_install
- cpu_only

Выбор сценария в проекте делается через группу, в которую помещен хост:
- если хост находится в wsl2_gpu, для него используется WSL2 GPU-сценарий;
- если хост находится в cloud_gpu_ready, используется профиль для уже подготовленного cloud GPU;
- если хост находится в cloud_gpu_install, используется профиль для cloud GPU с установкой стека проектом;
- если хост находится в cpu_only, используется CPU-only профиль.

## Пример выбора сценария
Для того, чтобы использовать определенный сценарий необходимо в `hosts.ini` прописать сценарий и указать хоста:

```yaml
[llm_nodes:children]
wsl2_gpu
cloud_gpu_ready
cloud_gpu_install
cpu_only

[cpu_only]
cpu-host ansible_host=192.168.56.50 ansible_user=Alexander
```

Можно делать более хитрее и сразу прописать все 4 сценария, но просто не прописывать хосты:

```yaml
[llm_nodes:children]
wsl2_gpu
cloud_gpu_ready
cloud_gpu_install
cpu_only

[wsl2_gpu]
#wsl-host ansible_host=TARGET_IP ansible_user=USER_NAME

[cloud_gpu_ready]
#gpu-ready-host ansible_host=TARGET_IP ansible_user=USER_NAME

[cloud_gpu_install]
#gpu-empty-host ansible_host=TARGET_IP ansible_user=USER_NAME

[cpu_only]
cpu-host ansible_host=192.168.56.50 ansible_user=Alexander
```

---

# Как работает выбор переменных

В проекте переменные разделены на 2 уровня:

- `group_vars/all.yml` — общие переменные для всех хостов;
- `group_vars/<scenario>.yml` — переменные конкретного сценария:
  - `wsl2_gpu.yml`
  - `cloud_gpu_ready.yml`
  - `cloud_gpu_install.yml`
  - `cpu_only.yml`
 
В `group_vars/all.yml` лежат базовые настройки проекта, например:
- флаги установки Docker и monitoring;
- параметры Python runtime;
- настройки Ollama;
- список моделей;
- настройки Garak;
- параметры LangChain;
- настройки platform users.

В сценарных файлах лежат только отличия между профилями, например:

- нужен ли GPU;
- должен ли проект ставить NVIDIA driver;
- должен ли проект ставить Docker;
- нужен ли nvidia_container_toolkit;
- использовать ли GPU в Ollama;
- включать ли cadvisor.

На практике это выглядит так:

- all.yml задает общее поведение проекта;
- cpu_only.yml отключает GPU-логику;
- wsl2_gpu.yml оставляет GPU, но запрещает установку host driver внутри WSL2;
- cloud_gpu_ready.yml предполагает, что часть GPU/Docker-стека уже подготовлена;
- cloud_gpu_install.yml включает наиболее полный путь установки.

Дополнительно в `site.yml` есть вычисляемые переменные из `pre_tasks`, которые влияют на запуск ролей:
- выбирается Python strategy;
- формируется selected_python_bin;
- выводится итоговая стратегия перед основным выполнением.

# Python strategy
В проекте выбор Python управляется переменной `llm_python_mode`. Она задается в `group_vars/all.yml`.
Поддерживаются 3 режима:

- `auto`
- `custom`
- `system`

Что означает каждый режим:

- `auto` — проект сам решает, какой Python использовать;
- `custom` — всегда использовать кастомный Python;
- `system` — всегда использовать системный python3.

Логика режима auto в текущем проекте такая:
- для Ubuntu ниже 24.04 выбирается кастомный Python;
- для Ubuntu 24.04 и выше выбирается системный Python.

В `pre_tasks` playbook делает 2 шага:

1. вычисляет `llm_use_custom_python`;
2. на его основе выбирает `llm_selected_python_binary`.

В проекте заранее заданы оба пути:

- системный Python: `/usr/bin/python3`
- кастомный Python: `/opt/python311/bin/python3.11`

Кастомный Python в проекте — это:
- версия `3.11.9`;
- установка в prefix `/opt/python311`;
- опциональный symlink `/usr/local/bin/python3.11`.

Где эта стратегия реально используется:
- роль `python_runtime` запускается только если нужен кастомный Python;
- `garak_runner` получает и `custom`, и `system` бинарник через переменные;
- `langchain_runtime` использует уже выбранный `llm_selected_python_binary`.

---

# Быстрый старт

Что нужно подготовить перед запуском:
- Linux/macOS/WSL с установленным `ansible`;
- доступ по SSH к целевому хосту;
- пользователь на хосте, от имени которого Ansible сможет подключиться;
- заполненный `inventory/hosts.ini` с хостом в нужной группе сценария.

Минимальный порядок действий:
- клонировать репозиторий;
- открыть `inventory/hosts.ini`;
- добавить свой хост в нужную группу;
- запустить основной playbook `site.yml`.

Пример:
```bash
git clone https://github.com/Tilteeed/llm.v2.git #Клонируем проект
cd llm.v2
nano inventory/hosts.ini #Изменяем хосты и выбираем сценарии
ansible-playbook site.yml #Запускаем плейбук
```
---

# Роли проекта

В `site.yml` сейчас подключены **13 ролей**:

- `ubuntu_base`
- `ubuntu_base_nvidia_host`
- `docker_engine`
- `nvidia_container_toolkit`
- `python_runtime`
- `ollama_container`
- `ollama_pull_models`
- `monitoring_stack`
- `garak_runner`
- `langchain_runtime`
- `platform_users`
- `python_project_packages`
- `ollama_webui`

`ubuntu_base`:
- базовая подготовка Ubuntu;
- обновление `apt` cache;
- установка базовых пакетов и Python tooling;
- опциональный `dist-upgrade`.

`ubuntu_base_nvidia_host`
- роль для GPU-хоста;
- проверяет доступность GPU;
- в обычном Linux-сценарии может ставить NVIDIA driver;
- в WSL2 работает в отдельном совместимом режиме.
- в WSL2 дополнительно создаёт symlink `nvidia-smi`, чтобы команда была доступна как обычная системная команда.
        
`docker_engine`
- подключает официальный Docker repository;
- ставит Docker Engine и compose plugin;
- запускает и включает Docker service;
- добавляет существующих пользователей в группу `docker`.

`nvidia_container_toolkit`
- ставит `nvidia-container-toolkit`;
- настраивает Docker runtime через `nvidia-ctk`;
- подготавливает хост к запуску GPU-контейнеров.

`python_runtime`
- собирает отдельный Python из исходников;
- устанавливает его в отдельный prefix;
- не заменяет системный `/usr/bin/python3`;
- при необходимости создает отдельный `venv`.

`python_project_packages`
- роль для установки дополнительных Python библиотек проекта;
- использует Python, выбранный общей Python strategy проекта;
- создает отдельный project venv;
- устанавливает дополнительные пакеты через pip;
- список пакетов задается переменной `llm_python_extra_packages`.

`ollama_container`
- создает каталоги и Docker network;
- шаблонизирует compose-файл;
- запускает контейнер `Ollama`;
- проверяет доступность Ollama API.

`ollama_pull_models`
- проверяет, что контейнер Ollama запущен;
- получает текущий список моделей;
- подтягивает только недостающие модели;
- показывает итоговый список после синхронизации.

`monitoring_stack`
- разворачивает monitoring через Docker Compose;
- шаблонизирует конфиг `Prometheus`;
- поднимает `Grafana`;
- проверяет доступность Prometheus и Grafana.

`garak_runner`
- выбирает Python для Garak;
- создает отдельный `venv`;
- устанавливает пакет `garak`;
- создает helper-скрипт для запуска проверок против Ollama.

`langchain_runtime`
- создает отдельный `venv` для LangChain;
- обновляет `pip` stack;
- ставит LangChain-пакеты;
- делает import-проверку `langchain`, `langchain_community` и `langgraph`.

`platform_users`
- создает пользователей;
- добавляет их в `sudo` и `docker`;
- может создавать общую группу;
- может создавать общий каталог для командной работы.

---

# Проверки после установки

- После выполнения playbook проверь, что в `PLAY RECAP` нет `failed`.
    
- Дальше проверь ключевые компоненты: Docker, Ollama, monitoring, Garak, LangChain и platform users. В проекте именно эти части поднимаются и валидируются ролями `ollama_container`, `monitoring_stack`, `garak_runner`, `langchain_runtime` и `platform_users`.
    
- **Docker**
    - Docker должен отвечать без ошибок.
        
```bash
docker version  
docker info
```

- **Ollama**
    
    - контейнер должен быть запущен;
        
    - API на `11434` должен отвечать.
        
    - В проекте порт Ollama по умолчанию — `11434`, base dir — `/opt/llm/ollama`.
        
```bash
docker ps  
curl http://127.0.0.1:11434/api/tags
```

- **Monitoring**
    
    - Prometheus должен отвечать на `9090`;
        
    - Grafana должна открываться на `3000`.
        
    - В проекте monitoring stack живет в `/opt/llm/monitoring`, а порты по умолчанию — `9090` для Prometheus и `3000` для Grafana.
        
```
docker ps  
curl http://127.0.0.1:9090/-/ready  
curl -I http://127.0.0.1:3000
```

- **Garak**
    
    - роль Garak сначала проверяет выбранный Python;
        
    - затем проверяет `venv`;
        
    - после этого создает отдельное окружение и валидирует запуск `garak`.
        
    - Пути проекта:
        
        - base dir: `/opt/llm/garak`
            
        - venv: `/opt/llm/garak/venv`
            
        - reports: `/opt/llm/garak/reports`
            
        - helper script: `/opt/llm/garak/bin/run_garak_ollama.sh`
            
- **Проверка Garak при system Python**

```bash
/usr/bin/python3 --version  
/usr/bin/python3 -m venv --help  
/opt/llm/garak/venv/bin/garak --help
```

- **Проверка Garak при custom Python**

```bash
/opt/python311/bin/python3.11 --version  
/opt/python311/bin/python3.11 -m venv --help  
/opt/llm/garak/venv/bin/garak --help
```

В проекте системный Python задан как `/usr/bin/python3`, а кастомный — как `/opt/python311/bin/python3.11`.

- **LangChain**
    
    - роль LangChain тоже работает через отдельный `venv`;
        
    - перед установкой она проверяет выбранный Python;
        
    - после установки делает import-check для `langchain`, `langchain_community` и `langgraph`.
        
    - Путь venv в проекте:
        
        - `/opt/venvs/langchain311`
            
- **Проверка LangChain при system Python**

```bash
/usr/bin/python3 --version  
/opt/venvs/langchain311/bin/python -c "import langchain; import langchain_community; import langgraph; print('langchain stack import ok')"
```

- **Проверка LangChain при custom Python**

```bash
/opt/python311/bin/python3.11 --version  
/opt/venvs/langchain311/bin/python -c "import langchain; import langchain_community; import langgraph; print('langchain stack import ok')"
```    

Сами пакеты LangChain в проекте ставятся в отдельный venv, а не в system Python напрямую.

- **Platform users**
    
    - должны существовать группы `sudo` и `docker`;
        
    - нужные пользователи должны быть созданы и добавлены в эти группы;
        
    - shared directory по умолчанию — `/opt/llm/shared`.
        
```bash
getent group sudo  
getent group docker  
id Alex  
ls -ld /opt/llm/shared
```

- **Минимальный чек-лист**
    
    - Docker работает;
        
    - `Ollama` отвечает на `http://127.0.0.1:11434/api/tags`;
        
    - `Prometheus` отвечает на `9090`;
        
    - `Grafana` отвечает на `3000`;
        
    - `garak` запускается из `/opt/llm/garak/venv`;
    
    - Ollama Web UI открывается на `http://<host>:8000`;
        
    - LangChain imports проходят из `/opt/venvs/langchain311`;
        
    - platform users и shared directory созданы.
 
---

# Monitoring

- Проект разворачивает **monitoring stack через Docker Compose**.
    
- В текущем виде в README лучше фиксировать только то, что реально используется и проверяется во время установки:
    
    - **Prometheus** — сбор метрик;
        
    - **Grafana** — визуализация и dashboards;
        
    - **node_exporter** — метрики хоста.
        
- Базовый каталог monitoring stack:
    
```bash
/opt/llm/monitoring
```

- Основные сервисы и порты:
    
    - **Prometheus**
        
        - порт: `9090`
            
        - endpoint: `http://<host>:9090`
            
    - **Grafana**
        
        - порт: `3000`
            
        - endpoint: `http://<host>:3000`
            
- Проверить запущенные контейнеры:
    
```bash
docker ps
```

- Проверка готовности Prometheus:
    
```bash
curl http://127.0.0.1:9090/-/ready
```

- Проверка Grafana:
    
```bash
curl -I http://127.0.0.1:3000
```

- В конфигурации monitoring stack имеет смысл ориентироваться на:
    
    - `Prometheus`;
        
    - `Grafana`;
        
    - `node_exporter`;
        
    - метрики `Ollama`, если они доступны в текущем окружении.
        
- Упрощенно monitoring в проекте выглядит так:
    

```bash
node_exporter ──► Prometheus ──► Grafana
```

- Где находятся основные файлы monitoring stack:
    
    - Docker Compose:
        
```bash
/opt/llm/monitoring/docker-compose.yml
```

- конфиг Prometheus:
    

/opt/llm/monitoring/prometheus/prometheus.yml

- provisioning Grafana:
    
```bash
/opt/llm/monitoring/grafana/provisioning
```

- Если monitoring уже развернут, для перезапуска можно использовать:
    
```bash
cd /opt/llm/monitoring  
docker compose restart
```

- Если нужно пересоздать stack:

```bash
cd /opt/llm/monitoring  
docker compose down  
docker compose up -d
```

---

# Ollama

В проекте `Ollama` разворачивается **как Docker-контейнер**, а не как systemd-service или ручная установка в хостовую систему. Для этого используется отдельная роль `ollama_container`, а загрузка моделей вынесена в отдельную роль `ollama_pull_models`.
    
Базовые пути `Ollama` в проекте:
    
- base dir:        

```bash
/opt/llm/ollama
```

- compose dir:
    

```bash
/opt/llm/ollama/compose
```

- data dir:
    
```bash
/opt/llm/ollama/data
```

- compose file:
    

```bash
/opt/llm/ollama/compose/compose.yml
```

Эти пути заданы через `ollama_container_base_dir`, `ollama_container_compose_dir`, `ollama_container_data_dir` и `ollama_container_compose_file`.

- Основные параметры контейнера:
    
    - имя контейнера: `ollama`
        
    - образ: `ollama/ollama:latest`
        
    - Docker network: `llm_stack_net`
        
    - bind address: `0.0.0.0`
        
    - host port: `11434`
        
    - internal port: `11434`
        
    - policy перезапуска: `unless-stopped`
        
- Как `Ollama` запускается в проекте:
    
    - Ansible сначала проверяет `docker version` и `docker info`;
        
    - при GPU-режиме дополнительно проверяет `nvidia-ctk --version`;
        
    - создает каталоги;
        
    - при необходимости создает Docker network;
        
    - шаблонизирует compose-файл;
        
    - заранее делает `docker pull ollama/ollama:latest`;
        
    - поднимает контейнер через `docker compose up -d`;
        
    - ждет, пока API на `/api/tags` начнет отвечать `200`.
        
- Где хранятся данные и модели:
    
    - внутри контейнера используется путь:
        
```bash
/root/.ollama
```

- на хосте он смонтирован в:
    
```bash
/opt/llm/ollama/data
```

То есть модели и служебные данные `Ollama` сохраняются на хосте в `/opt/llm/ollama/data`.

- Проверка контейнера:
    
```bash
docker ps  
docker inspect -f '{{.State.Running}}' ollama
```

В самой роли именно состояние `running=true` считается успешной проверкой запуска.

- Проверка API:
    
```bash
curl http://127.0.0.1:11434/api/tags
```

В проекте это основной health-check `Ollama` после старта контейнера.

- Работа с моделями вынесена в отдельную роль:
    
    - сначала проверяется, что контейнер существует и реально запущен;
        
    - затем проверяется доступность API;
        
    - после этого Ansible выполняет `ollama list` внутри контейнера;
        
    - сравнивает уже существующие модели со списком из переменных;
        
    - подтягивает только недостающие модели через `ollama pull`.
        
- Список моделей по умолчанию сейчас такой:

```bash
ollama_pull_models_list:  
  - smollm:135m
```

В `group_vars/all.yml` также оставлены закомментированные примеры для `qwen2.5:7b` и `llama3.1:8b`.

- Проверка списка моделей:

```bash
docker exec ollama ollama list
```

- Ручная загрузка модели:
    
```bash
docker exec ollama ollama pull smollm:135m
```

Именно такой подход использует и сама роль `ollama_pull_models` — через `docker exec <container> ollama pull <model>`.

- Если нужен GPU-режим:
    
    - в проекте он управляется переменной `ollama_container_use_gpu`;
        
    - при включенном GPU в compose добавляется reservation device с `driver: nvidia`, `count: all`, `capabilities: [gpu]`.
 
---
# Ollama Web UI

В проекте дополнительно разворачивается веб-интерфейс для Ollama на базе проекта `ollama-webui`.

Он позволяет:

- работать с моделями Ollama через браузер;
- отправлять запросы к моделям;
- просматривать историю диалогов;
- управлять доступом пользователей.

Web UI разворачивается отдельной ролью: `ollama_webui`

Контейнер Web UI подключается к той же Docker network, что и контейнер Ollama (`llm_stack_net`), и взаимодействует с ним через внутренний API.

Основные параметры Web UI:

- контейнер: `ollama-webui`
- образ: `ghcr.io/ollama-webui/ollama-webui:main`
- порт: `8000`
- Docker network: `llm_stack_net`

Основные пути:
- Main dir: `/opt/llm/ollama-webui`
- Compose dir: `/opt/llm/ollama-webui/compose`
- Data dir: `/opt/llm/ollama-webui/data`

Данные Web UI (пользователи, настройки, история) сохраняются в каталоге:
- `/opt/llm/ollama-webui/data`

## Доступ к Web UI

После развёртывания интерфейс доступен по адресу:
```bash
http://<host>:8000
```
Например:
```bash
http://10.8.1.1:8000
```

## Первый вход

При первом запуске Web UI не имеет заранее созданных учетных записей.

Первый зарегистрированный пользователь автоматически получает роль администратора.

Для начала работы необходимо:

1. открыть страницу Web UI;
2. нажать **Sign up**;
3. создать первый аккаунт администратора.

После этого можно добавлять других пользователей.

## Проверка Web UI

Проверить контейнер:
```bash
docker ps
```

Проверить HTTP доступность:
```bash
curl -I http://127.0.0.1:8000
```

или

```bash
curl -I http://10.8.1.1:8000
```

---

# Garak

Garak в проекте ставится в отдельный venv, а не в системный Python напрямую. Роль garak_runner сначала выбирает Python-бинарник, затем проверяет python --version, проверяет python -m venv, создает окружение, ставит туда garak и валидирует запуск через garak --help.

Выбор Python для Garak идет не сам по себе, а через общую Python strategy проекта:etuptools/wheel`, устанавливает `garak` и делает smoke-check через `garak --help`.

Выбор Python для `Garak` идет **не сам по себе**, а через общую Python strategy проекта:
    
- `llm_python_mode: auto`
        
  - Ubuntu **ниже 24.04** → используется **кастомный Python**
            
  - Ubuntu **24.04 и выше** → используется **системный Python**
            
- `llm_python_mode: custom` → всегда кастомный Python
        
- `llm_python_mode: system` → всегда системный Python.
        
Пути Python в проекте:
- system Python:
```bash
/usr/bin/python3
```
- custom Python:

```bash
/opt/python311/bin/python3.11
```

Эти пути заданы в `group_vars/all.yml`, а в `site.yml` выбранный вариант передается в роль `garak_runner`.

Основные пути Garak:
    
- base dir:
        
```bash
/opt/llm/garak
```

- venv:
    
```bash
/opt/llm/garak/venv
```

- reports:
    
```bash
/opt/llm/garak/reports
```

- bin:
    
```bash
/opt/llm/garak/bin
```

- helper script:
    
```
/opt/llm/garak/bin/run_garak_ollama.sh
```

Эти пути заданы в `group_vars/all.yml`.
- Версия пакета в проекте сейчас зафиксирована:
    
```bash
garak==0.14.0
```

- Также для установки используется отдельный pip cache:

```bash
/opt/llm/pip-cache
```
Это тоже задается через `group_vars/all.yml`.

- Что делает роль `garak_runner`:
    
    - проверяет выбранный Python через `--version`;
        
    - проверяет наличие `python -m venv`;
        
    - проверяет доступность `Ollama API` на `/api/tags`;
        
    - создает каталоги Garak;
        
    - создает `venv`;
        
    - обновляет `pip`-стек;
        
    - устанавливает `garak`;
        
    - проверяет, что бинарник `garak` реально появился в `venv`;
        
    - валидирует запуск `garak --help`;
        
    - создает helper-скрипт для ручного запуска против Ollama.
        
Проверка Garak при **system Python**:

```bash
/usr/bin/python3 --version  
/usr/bin/python3 -m venv --help  
/opt/llm/garak/venv/bin/garak --help
```

Проверка Garak при **custom Python**:

```bash
/opt/python311/bin/python3.11 --version  
/opt/python311/bin/python3.11 -m venv --help  
/opt/llm/garak/venv/bin/garak --help
```

Сам `garak` в обоих случаях запускается уже из отдельного `venv`.

Связка с Ollama в проекте:
- базовый URL для Garak:
        
```bash
http://127.0.0.1:11434
```

Модель по умолчанию:
    
```bash
qwen2.5:7b
```

Эти значения берутся из `garak_runner_ollama_base_url` и `garak_runner_default_model`.

Для ручного запуска роль создает helper-скрипт:
    
```bash
/opt/llm/garak/bin/run_garak_ollama.sh
```

Примеры использования helper-скрипта:
    
```bash
/opt/llm/garak/bin/run_garak_ollama.sh  
/opt/llm/garak/bin/run_garak_ollama.sh qwen2.5:7b  
/opt/llm/garak/bin/run_garak_ollama.sh llama3.1:8b
```

По шаблону скрипт активирует `venv`, создает каталог отчетов и запускает `garak` с `--model_type openai`, `--model_name`, `--seed 42` и `--report_prefix` в каталоге отчетов.

Где искать результаты запусков:
    
```bash
/opt/llm/garak/reports
```

Именно туда helper-скрипт пишет отчеты Garak.

---

# LangChain

`LangChain` в проекте ставится в **отдельный `venv`**, а не в системный Python напрямую. Роль `langchain_runtime` сначала проверяет, что нужный Python уже существует, затем создает отдельное окружение, обновляет `pip/setuptools/wheel`, устанавливает пакеты и в конце делает import-check.

Выбор Python для `LangChain` завязан на **общую Python strategy проекта**:

  * `llm_python_mode: auto`

    * Ubuntu **20.04** → используется **кастомный Python**
    * Ubuntu **выше 22.04** → используется **системный Python**
  * `llm_python_mode: custom` → всегда кастомный Python
  * `llm_python_mode: system` → всегда системный Python.

* Пути Python в проекте:

  * system Python:

```bash
/usr/bin/python3
```

* custom Python:

```bash
/opt/python311/bin/python3.11
```

Эти пути заданы в общих переменных проекта и используются при выборе runtime для `LangChain`.

* Основной путь LangChain runtime:

  * venv:

```bash
/opt/venvs/langchain311
```

Этот путь задается через `langchain_runtime_venv_path`.

* Какие пакеты ставятся по умолчанию:

```yaml
langchain_runtime_packages:
  - langchain
  - langchain-community
  - langgraph
```

Дополнительные пакеты можно добавить через `langchain_runtime_extra_packages`, который сейчас по умолчанию пустой.

* Что делает роль `langchain_runtime`:

  * проверяет выбранный Python через `--version`;
  * создает родительский каталог для `venv`;
  * создает отдельный `venv`;
  * приводит права на каталог к нужному состоянию;
  * обновляет `pip/setuptools/wheel`;
  * устанавливает LangChain-стек;
  * проверяет импорты внутри `venv`.

* Проверка LangChain при **system Python**:

```bash
/usr/bin/python3 --version
/opt/venvs/langchain311/bin/python -c "import langchain; import langchain_community; import langgraph; print('langchain stack import ok')"
```

Для Ubuntu, где в `auto`-режиме выбирается системный Python, именно он используется для создания `venv`, а сами пакеты потом работают уже внутри `/opt/venvs/langchain311`.

* Проверка LangChain при **custom Python**:

```bash
/opt/python311/bin/python3.11 --version
/opt/venvs/langchain311/bin/python -c "import langchain; import langchain_community; import langgraph; print('langchain stack import ok')"
```

Для Ubuntu 20.04 в `auto`-режиме проект использует кастомный Python 3.11, а затем создает на нем отдельный `venv` для LangChain.

---

# Platform users

Роль `platform_users` отвечает за создание и настройку пользователей платформы на целевом хосте. Она не просто создает аккаунты, а сразу проверяет входные данные, наличие системных групп и при необходимости подготавливает общую группу и общий каталог для работы команды. ([GitHub][1])

Что делает роль:

  * проверяет, что `platform_users_list` задан и не пустой;
  * проверяет наличие системных групп `docker` и `sudo`;
  * при необходимости создает общую группу команды;
  * создает пользователей с домашними каталогами;
  * добавляет пользователей в нужные группы;
  * при необходимости создает общий каталог для совместной работы. ([GitHub][1])

Список пользователей по умолчанию задается в `group_vars/all.yml` через `platform_users_list`. Сейчас там описаны:

  * `Alex`
  * `IvanO`
  * `IvanM`
  * `ilya`
  * `Dima`

Для каждого пользователя задаются:

  * `name`
  * `comment`
  * `shell`
  * `password_hash`

Роль ожидает именно **хэш пароля**, а не открытый пароль. В текущем репозитории везде стоит заглушка `REPLACE_ME`, то есть перед реальным использованием эти значения нужно заменить.

Домашние каталоги для пользователей включены:

```yaml
platform_users_create_home: true
```

Обновление пароля настроено так:

```yaml
platform_users_update_password: on_create
```

Это значит, что пароль задается при создании пользователя и не перезаписывается на каждом прогоне.

Базовые дополнительные группы для пользователей:

```yaml
platform_users_default_groups:
  - sudo
  - docker
```

То есть создаваемые пользователи получают административные права и доступ к Docker.

В проекте также включена общая группа команды:

```yaml
platform_users_create_shared_group: true
platform_users_shared_group_name: llm-admins
platform_users_add_shared_group: true
```

Если этот режим включен, роль добавляет `llm-admins` к стандартным группам `sudo` и `docker`, и пользователи получают еще и общий групповой контур доступа.

Общий каталог команды тоже включен:

```bash
/opt/llm/shared
```

Его параметры по умолчанию:

* owner: `root`

* group: `llm-admins`

* mode: `2775`
Режим `2775` нужен для `setgid`, чтобы новые файлы наследовали групповую принадлежность каталога.

Если упростить итоговую модель доступа:

  * пользователи создаются как обычные локальные Linux-аккаунты;
  * каждому создается home directory;
  * пользователи добавляются в `sudo` и `docker`;
  * дополнительно они попадают в `llm-admins`;
  * для командной работы используется общий каталог `/opt/llm/shared`.

Что проверить после применения роли:

```bash
getent group sudo
getent group docker
getent group llm-admins
id Alex
ls -ld /opt/llm/shared
```

Эти проверки соответствуют логике самой роли: она ожидает, что группы существуют, пользователи созданы, а общий каталог подготовлен. 

---

Согласен — в README лучше **не делать вид, что Vault уже используется**, а честно написать, что пока секреты не вынесены и что это направление для будущего развития. Вот аккуратный раздел.

---

# Секреты и Vault

В текущей версии проекта **Ansible Vault не используется**.

Все переменные проекта находятся в открытом виде в `group_vars/`.

Это сделано сознательно, потому что:

  * проект пока используется в тестовой или лабораторной среде;
  * секреты в переменных отсутствуют;
  * большинство параметров — это инфраструктурные настройки.

Например, в `platform_users_list` сейчас используются заглушки:

```yaml
password_hash: "REPLACE_ME"
```

Это означает, что перед реальным использованием пароли должны быть заменены на реальные **hash значения**, а не храниться в открытом виде.

Если проект будет использоваться в более серьезной инфраструктуре, имеет смысл:

  * вынести чувствительные данные в **Ansible Vault**;
  * хранить секреты отдельно от обычных переменных.

Типичные кандидаты для Vault в будущем:

  * `password_hash` пользователей;
  * API-токены;
  * credentials для сервисов;
  * registry credentials;
  * SSH private keys.

Пример создания Vault-файла:

```bash
ansible-vault create group_vars/vault.yml
```

Пример редактирования:

```bash
ansible-vault edit group_vars/vault.yml
```

Пример запуска playbook с Vault:

```bash
ansible-playbook site.yml --ask-vault-pass
```

Возможная структура в будущем:

```
group_vars/
├── all.yml
├── cpu_only.yml
├── cloud_gpu_install.yml
├── cloud_gpu_ready.yml
├── wsl2_gpu.yml
└── vault.yml
```

В таком случае:
  * обычные переменные останутся в `group_vars`;
  * чувствительные данные будут храниться в `vault.yml`.

---

# Типичные проблемы

* Ниже приведены проблемы, которые чаще всего могут возникнуть при развёртывании или использовании проекта.

---
## Ollama Web UI не открывается

**Симптомы**

```bash
curl -I http://127.0.0.1:8000 => Возвращает ошибку или таймаут.
```

или

```bash
curl -I http://10.8.1.1:8000 => Возвращает ошибку или таймаут.
```

**Что проверить**
Проверить, что контейнер ollama-webui запущен и что порт 8000 не занят другим сервисом.

```bash
docker ps
docker logs ollama-webui
ss -tulpn | grep 8000
```

## Ollama Web UI открывается, но не работает с моделями

**Симптомы**

Web UI открывается, но список моделей пустой или запросы к модели завершаются ошибкой.

**Что проверить**

- контейнер `ollama` запущен;
- контейнер `ollama-webui` подключен к сети `llm_stack_net`;
- `Ollama API` доступен:

```bash
curl http://127.0.0.1:11434/api/tags
```

или

```bash
curl http://10.8.1.1:8000/api/tags
```

Проверить логи:
```bash
docker logs ollama
docker logs ollama-webui
```

## В WSL2 команда nvidia-smi не находится

**Симптомы**

```bash
nvidia-smi => Возвращает ошибку command not found
```

**Причина:**
В WSL2 бинарник NVIDIA может находиться по пути:
```bash
/usr/lib/wsl/lib/nvidia-smi
```

**Решение:**
Запустить роль GPU-подготовки проекта и проверить, что создан symlink:
```bash
ls -l /usr/bin/nvidia-smi
nvidia-smi
```

## Дополнительные Python пакеты проекта не установились

**Симптомы**

Пакеты из `llm_python_extra_packages` отсутствуют в project venv.

**Что проверить**

- выбранный Python существует;
- project venv создан;
- список пакетов задан в `group_vars/all.yml`.

Проверка:

```bash
/opt/venvs/project311/bin/python --version
/opt/venvs/project311/bin/pip list
```

## Ansible не может подключиться к хосту

**Симптомы**

```text
UNREACHABLE! => Failed to connect to the host via ssh
```

**Что проверить**

* хост доступен по сети;
* указан правильный `ansible_host`;
* указан правильный `ansible_user`;
* SSH доступ работает вручную.

```bash
ssh user@host
```

inventory содержит правильную запись:

```ini
cpu-host ansible_host=192.168.56.50 ansible_user=alex
```

---

## Ошибка `sudo` во время выполнения playbook

**Симптомы**

```text
FAILED! => Missing sudo password
```

**Причина**

Playbook использует `become: true`.

**Решение**

Запускать playbook с вводом пароля `sudo`:

```bash
ansible-playbook site.yml
```

Ansible сам запросит пароль, так как в `ansible.cfg` включено:

```ini
become_ask_pass = True
```

---

## Docker установлен, но пользователь не может им пользоваться

**Симптомы**

```bash
permission denied while trying to connect to the Docker daemon
```

**Причина**

Пользователь еще не получил новую группу `docker`.

**Решение**

Перелогиниться:

```bash
logout
login
```

или выполнить:

```bash
newgrp docker
```

Проверить:

```bash
groups
```

---

## Ollama контейнер запущен, но API не отвечает

**Симптомы**

```bash
curl http://127.0.0.1:11434/api/tags
```

возвращает ошибку.

**Что проверить**

```bash
docker ps
```

Проверить логи контейнера:

```bash
docker logs ollama
```

Если контейнер не запущен:

```bash
cd /opt/llm/ollama/compose
docker compose up -d
```

---

## Ollama работает, но нет моделей

**Симптомы**

```bash
docker exec ollama ollama list
```

показывает пустой список.

**Причина**

Модели не были загружены.

**Решение**

```bash
docker exec ollama ollama pull smollm:135m
```

или перезапустить роль загрузки моделей:

```bash
ansible-playbook site.yml --tags ollama_pull_models
```

---

## Garak не запускается

**Симптомы**

```bash
/opt/llm/garak/venv/bin/garak --help
```

возвращает ошибку.

**Что проверить**

Проверить Python runtime:

```bash
/usr/bin/python3 --version
```

или

```bash
/opt/python311/bin/python3.11 --version
```

Проверить venv:

```bash
ls /opt/llm/garak/venv
```

Если окружение повреждено, можно пересоздать его через Ansible:

```bash
ansible-playbook site.yml
```

---

## LangChain не импортируется

**Симптомы**

```bash
ModuleNotFoundError: No module named 'langchain'
```

**Причина**

Пакеты установлены только внутри `venv`.

**Правильная проверка**

```bash
/opt/venvs/langchain311/bin/python -c "import langchain"
```

---

## GPU не виден внутри контейнеров

**Симптомы**

```bash
nvidia-smi
```

работает на хосте, но GPU не виден внутри контейнера.

**Что проверить**

Проверить NVIDIA runtime:

```bash
nvidia-ctk --version
```

Проверить Docker runtime:

```bash
docker info | grep -i nvidia
```

---

## Python strategy выбрала не тот Python

**Симптомы**

роль `python_runtime` запускается или пропускается неожиданно.

**Причина**

режим `llm_python_mode: auto`.

**Как проверить**

В начале playbook выводится выбранная стратегия.

Если нужно принудительно изменить поведение, можно задать:

```yaml
llm_python_mode: system
```

или

```yaml
llm_python_mode: custom
```

в `group_vars`.

---

# Дальнейшее развитие

Проект можно развивать дальше, например:

добавить **Ansible Vault** для хранения секретов;

добавить **CI/CD pipeline** для проверки playbook;

добавить больше **monitoring dashboards**;

расширить поддержку **GPU-сценариев**;

добавить **дополнительные LLM runtime**;

автоматизировать **обновление моделей**;

добавить **автоматические security проверки LLM** через Garak;

расширить runtime окружение для **LangChain приложений**.

реализовать HTTPS + Nginx.


