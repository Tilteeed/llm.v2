# Что это за проект?

`llm.v2` — это Ansible-проект для подготовки Ubuntu-хоста под LLM workloads и связанные сервисы.

Проект запускается через основной playbook `site.yml` и работает с группой хостов `llm_nodes`.

Главный рабочий сценарий сейчас — `urfu-server`. Он описывает GPU-сервер, на котором разворачиваются:
- базовая подготовка Ubuntu;
- Docker и NVIDIA Container Toolkit;
- контейнерный `Ollama`;
- загрузка моделей в Ollama;
- RAG-agent backend;
- Open WebUI с Nemo Guardrails;
- self-hosted Langfuse для LLM-observability;
- Prometheus, Grafana, node-exporter и cAdvisor;
- Python runtime и Python-пакеты проекта;
- Garak runner;
- LangChain runtime;
- platform users.

По сути, это единая инфраструктурная точка входа для развёртывания LLM-полигона через Ansible.

Проект не просто ставит отдельные пакеты, а собирает связку сервисов вокруг Ollama:

```text
Пользователь / API / Web UI
        │
        ├── Open WebUI + Nemo Guardrails ──► Ollama
        │
        └── RAG-agent ──► Ollama
              │
              └── Langfuse traces

Prometheus / Grafana отдельно смотрят инфраструктуру:
CPU, RAM, GPU, контейнеры, node-exporter, cAdvisor.
```

---

# Что разворачивает проект

- Базовую подготовку Ubuntu-хоста
  - обновление apt cache;
  - установку базовых системных пакетов;
  - установку Python tooling, который нужен Ansible-ролям;
  - подготовку хоста к дальнейшей настройке Docker, GPU и сервисов.

- GPU-стек для NVIDIA-хостов
  - проверку доступности GPU;
  - при необходимости установку NVIDIA driver;
  - пост-проверки через `nvidia-smi`;
  - отдельный WSL2-режим, где host driver внутри Ubuntu не ставится.

- Docker-инфраструктуру
  - подключение официального Docker repository;
  - установку Docker Engine и compose plugin;
  - запуск и включение Docker service;
  - подготовку хоста к запуску контейнерных сервисов.

- NVIDIA Container Toolkit
  - установку `nvidia-container-toolkit`;
  - настройку Docker runtime для GPU-контейнеров;
  - проверку того, что контейнеры могут видеть GPU.

- Отдельный Python runtime
  - сборку и установку отдельного Python из исходников;
  - установку в отдельный prefix;
  - работу без замены системного `/usr/bin/python3`;
  - при необходимости создание отдельных virtual environments.

- Общий project venv
  - установку дополнительных Python-пакетов проекта;
  - ML/LLMOps-зависимости;
  - пакеты для FastAPI, LangChain, обучения и дальнейших экспериментов.

- Ollama в контейнере
  - создание каталогов и Docker network;
  - генерацию docker compose конфигурации;
  - запуск контейнера Ollama;
  - проверку доступности Ollama API после запуска.

- Модели для Ollama
  - проверку уже загруженных моделей;
  - подтягивание недостающих моделей через `ollama pull`;
  - синхронизацию списка моделей, который задан переменными проекта.

- RAG-agent backend
  - клонирование внешнего репозитория `g1nry/rag_agent`;
  - overlay-патчинг исходников через Ansible;
  - сборку локального Docker-образа;
  - запуск API на `8000`;
  - подключение к Ollama;
  - подключение к Langfuse;
  - трейсинг `/api/v1/chat` и `/api/v1/rag/chat`.

- Open WebUI с Nemo Guardrails
  - клонирование проекта `phenkka/newWebLLM`;
  - сборку локального образа `open-webui-guardrails:local`;
  - запуск Open WebUI на `3030`;
  - подключение Web UI к Ollama;
  - подключение Nemo Guardrails внутри Web UI.

- Langfuse stack
  - развёртывание self-hosted Langfuse v3;
  - запуск `langfuse-web`, `langfuse-worker`, `postgres`, `clickhouse`, `redis`, `minio`;
  - создание организации, проекта, пользователя и API-ключей через bootstrap-переменные;
  - публикацию UI на `3001`;
  - подключение RAG-agent к Langfuse по внутреннему адресу `http://langfuse-web:3000`.

- Monitoring stack
  - развёртывание мониторинга через Docker Compose;
  - конфигурацию Prometheus;
  - запуск Grafana;
  - node-exporter для метрик хоста;
  - cAdvisor для метрик контейнеров;
  - provisioning datasource и dashboards.

- Garak
  - отдельное Python virtual environment;
  - установку пакета `garak`;
  - smoke-check CLI;
  - helper-скрипт для запуска проверок против Ollama endpoint.

- LangChain runtime
  - отдельный venv под LangChain;
  - установку пакетов `langchain`, `langchain-community`, `langgraph` и связанных зависимостей;
  - проверку импорта установленного Python-стека.

- Platform users
  - создание пользователей;
  - добавление их в группы `sudo` и `docker`;
  - при необходимости создание общей группы и общего каталога для командной работы.

---

# Поддерживаемые сценарии

Проект сейчас поддерживает несколько сценариев хостов:

- `wsl2_gpu`
- `cloud_gpu_ready`
- `cloud_gpu_install`
- `cpu_only`
- `urfu-server`

Все они входят в общую группу `llm_nodes`, на которую запускается основной `site.yml`.

## Сценарий `urfu-server`

Это основной сценарий, который сейчас используется чаще всего.

Хост:

```text
10.40.240.103
```

Inventory-группа:

```ini
[urfu-server]
gpu-ready-host ansible_host=10.40.240.103 ansible_user=malkerov
```

Особенности сценария:

- GPU-стек включен;
- Docker устанавливается и управляется проектом;
- NVIDIA host driver уже есть на хосте и проект его не трогает;
- NVIDIA Container Toolkit устанавливается и настраивается проектом;
- Ollama запускается с GPU;
- monitoring stack включает cAdvisor;
- node-exporter монтирует rootfs как `/:/host:ro`;
- RAG использует модель `qwen2.5:14b`;
- embeddings-модель — `nomic-embed-text:latest`;
- Open WebUI работает на `3030`;
- RAG-agent работает на `8000`;
- Langfuse работает на `3001`;
- Grafana остается на `3000`;
- Prometheus остается на `9090`.

## Сценарий `wsl2_gpu`

- Сценарий для WSL2 + GPU;
- GPU-стек включен;
- NVIDIA host driver внутри WSL2 не устанавливается;
- Docker управляется проектом;
- NVIDIA Container Toolkit управляется проектом;
- Ollama запускается с GPU;
- cAdvisor в monitoring stack отключен.

## Сценарий `cloud_gpu_ready`

- Сценарий для облачного GPU-хоста, где основная GPU/Docker-база уже готова;
- GPU-стек включен;
- Docker не устанавливается проектом;
- NVIDIA host driver не устанавливается;
- NVIDIA Container Toolkit не настраивается проектом;
- Ollama запускается с GPU;
- cAdvisor в monitoring stack включен.

## Сценарий `cloud_gpu_install`

- Сценарий для облачного GPU-хоста, который нужно подготовить почти с нуля;
- GPU-стек включен;
- Docker устанавливается и настраивается проектом;
- NVIDIA host driver устанавливается проектом;
- NVIDIA Container Toolkit устанавливается и настраивается проектом;
- Ollama запускается с GPU;
- cAdvisor в monitoring stack включен.

## Сценарий `cpu_only`

- Сценарий для хоста без GPU;
- GPU-стек отключен;
- NVIDIA driver и NVIDIA Container Toolkit не используются;
- Docker управляется проектом;
- Ollama запускается без GPU, в CPU-режиме;
- cAdvisor в monitoring stack отключен.

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
4. роли подключаются последовательно;
5. часть ролей включается или пропускается через `when`;
6. итоговая конфигурация зависит от группы хоста и переменных в `group_vars`.

По слоям проект можно читать так:

- слой хоста:
  - `ubuntu_base`
  - `ubuntu_base_nvidia_host`
  - `docker_engine`
  - `nvidia_container_toolkit`
  - `python_runtime`

- слой Python/пакетов:
  - `python_project_packages`
  - `langchain_runtime`
  - `garak_runner`

- слой LLM-сервисов:
  - `ollama_container`
  - `ollama_pull_models`
  - `rag_agent`
  - `open_webui_guardrails`

- слой observability/monitoring:
  - `langfuse_stack`
  - `monitoring_stack`

- слой доступа:
  - `platform_users`

Общая схема сервисов:

```text
                       ┌────────────────────┐
                       │      Пользователь  │
                       └─────────┬──────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
              ▼                                     ▼
   ┌─────────────────────┐              ┌─────────────────────┐
   │ Open WebUI + Nemo   │              │      RAG-agent      │
   │ :3030               │              │      :8000          │
   └──────────┬──────────┘              └──────────┬──────────┘
              │                                    │
              │                                    ├──► Langfuse :3001
              │                                    │    traces:
              │                                    │    rag-agent-chat
              │                                    │    rag-chat
              ▼                                    ▼
        ┌──────────────────────────────────────────────────┐
        │                    Ollama                        │
        │                    :11434                        │
        └──────────────────────────────────────────────────┘

        ┌──────────────────────────────────────────────────┐
        │ Monitoring: Prometheus :9090, Grafana :3000      │
        │ node-exporter :9100, cAdvisor :8081              │
        └──────────────────────────────────────────────────┘
```

Важно: Open WebUI сейчас **не подключён к Langfuse напрямую**. Langfuse покрывает RAG-agent API. Чаты, которые идут прямо через Open WebUI, пока не трейсируются в Langfuse. Подключение Open WebUI к Langfuse отложено как отдельная задача.

---

# Структура репозитория

```text
llm.v2/
├── group_vars/
│   ├── all.yml
│   ├── cloud_gpu_install.yml
│   ├── cloud_gpu_ready.yml
│   ├── cpu_only.yml
│   ├── urfu-server.yml
│   └── wsl2_gpu.yml
├── inventory/
│   └── hosts.ini
├── roles/
│   ├── docker_engine/
│   ├── garak_runner/
│   ├── langchain_runtime/
│   ├── langfuse_stack/
│   ├── monitoring_stack/
│   ├── nvidia_container_toolkit/
│   ├── ollama_container/
│   ├── ollama_pull_models/
│   ├── open_webui_guardrails/
│   ├── platform_users/
│   ├── python_project_packages/
│   ├── python_runtime/
│   ├── rag_agent/
│   ├── ubuntu_base/
│   └── ubuntu_base_nvidia_host/
├── README.md
├── ansible.cfg
└── site.yml
```

Что за что отвечает:

- `group_vars/` — общие и сценарные переменные проекта;
- `inventory/` — inventory с хостами и группами;
- `roles/` — вся основная логика развёртывания по компонентам;
- `ansible.cfg` — базовая конфигурация Ansible для этого репозитория;
- `site.yml` — главный playbook, который запускает роли проекта;
- `README.md` — документация проекта.

---

# Быстрый старт

Что нужно подготовить перед запуском:

- Linux/macOS/WSL с установленным `ansible`;
- доступ по SSH к целевому хосту;
- пользователь на хосте, от имени которого Ansible сможет подключиться;
- возможность выполнить `become`/`sudo`;
- заполненный `inventory/hosts.ini` с хостом в нужной группе сценария.

Минимальный порядок действий:

```bash
git clone https://github.com/Tilteeed/llm.v2.git
cd llm.v2
nano inventory/hosts.ini
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml
```

Для основного сценария `urfu-server` inventory выглядит так:

```ini
[llm_nodes:children]
wsl2_gpu
cloud_gpu_ready
cloud_gpu_install
cpu_only
urfu-server

[urfu-server]
gpu-ready-host ansible_host=10.40.240.103 ansible_user=malkerov
```

Так как в `ansible.cfg` включен `become_ask_pass`, при запуске playbook Ansible запросит пароль sudo:

```bash
ansible-playbook site.yml
```

Если нужно прогнать только отдельную часть, используются tags:

```bash
ansible-playbook site.yml --tags ollama
ansible-playbook site.yml --tags ollama_pull_models
ansible-playbook site.yml --tags langfuse
ansible-playbook site.yml --tags rag_agent
ansible-playbook site.yml --tags open_webui
ansible-playbook site.yml --tags monitoring
```

---

# Порядок ролей в site.yml

В `site.yml` роли идут в таком порядке:

1. `ubuntu_base`
2. `ubuntu_base_nvidia_host`
3. `docker_engine`
4. `nvidia_container_toolkit`
5. `python_runtime`
6. `python_project_packages`
7. `ollama_container`
8. `ollama_pull_models`
9. `langfuse_stack`
10. `rag_agent`
11. `open_webui_guardrails`
12. `monitoring_stack`
13. `garak_runner`
14. `langchain_runtime`
15. `platform_users`

Почему Langfuse стоит до RAG-agent:

- RAG-agent при сборке получает `LANGFUSE_*` переменные;
- внутри контейнера агент проверяет доступность Langfuse через SDK;
- если Langfuse уже поднят, `auth_check()` проходит сразу;
- после этого `/api/v1/chat` и `/api/v1/rag/chat` начинают отправлять traces.

Почему Open WebUI стоит после RAG-agent:

- Open WebUI является пользовательским интерфейсом;
- RAG-agent является backend-сервисом;
- оба используют Ollama, но Open WebUI сейчас не зависит от Langfuse.

---

# Карта портов

Основные сервисы и порты текущего стенда:

```text
11434  Ollama API
 8000  RAG-agent API
 3030  Open WebUI + Nemo Guardrails
 3001  Langfuse UI/API
 9090  Prometheus
 3000  Grafana
 9100  node-exporter
 8081  cAdvisor
```

Важно по конфликтам:

- `3000` занят Grafana;
- `3030` занят Open WebUI;
- `9090` занят Prometheus;
- поэтому Langfuse UI вынесен на `3001`.

Внутри Docker network `llm_stack_net` сервисы используют внутренние DNS-имена:

```text
ollama        -> http://ollama:11434
rag-agent     -> http://rag-agent:8000
langfuse-web  -> http://langfuse-web:3000
open-webui    -> http://open-webui:8080
```

---

# Выбор переменных

В проекте переменные разделены на 2 уровня:

- `group_vars/all.yml` — общие переменные для всех хостов;
- `group_vars/<scenario>.yml` — переменные конкретного сценария.

Для основного стенда используется:

```text
group_vars/urfu-server.yml
```

В `group_vars/all.yml` лежат базовые настройки проекта:

- флаги установки Docker и monitoring;
- параметры Python runtime;
- настройки Ollama;
- настройки RAG-agent;
- настройки Open WebUI;
- настройки Langfuse;
- настройки Garak;
- настройки LangChain;
- настройки platform users.

В `group_vars/urfu-server.yml` лежат переопределения для конкретного сервера:

- включенный GPU-стек;
- управление Docker;
- запрет на установку host NVIDIA driver;
- модели RAG;
- список моделей Ollama;
- секрет Open WebUI;
- секреты Langfuse;
- внешний адрес Langfuse.

Важно: реальные секреты в текущем виде временно находятся в `group_vars/urfu-server.yml`. Перед публикацией, передачей проекта или финальным использованием их нужно ротировать и вынести в Ansible Vault.

---

# Python strategy

В проекте выбор Python управляется переменной:

```yaml
llm_python_mode: auto
```

Поддерживаются 3 режима:

- `auto`
- `custom`
- `system`

Что означает каждый режим:

- `auto` — проект сам решает, какой Python использовать;
- `custom` — всегда использовать кастомный Python;
- `system` — всегда использовать системный `python3`.

Логика режима `auto`:

- для Ubuntu ниже 24.04 выбирается кастомный Python;
- для Ubuntu 24.04 и выше выбирается системный Python.

В `pre_tasks` playbook делает 2 шага:

1. вычисляет `llm_use_custom_python`;
2. на его основе выбирает `llm_selected_python_binary`.

В проекте заранее заданы оба пути:

```text
system Python: /usr/bin/python3
custom Python: /opt/python311/bin/python3.11
```

Кастомный Python в проекте:

- версия `3.11.9`;
- установка в prefix `/opt/python311`;
- опциональный symlink `/usr/local/bin/python3.11`.

Где эта стратегия реально используется:

- роль `python_runtime` запускается только если нужен кастомный Python;
- `python_project_packages` использует выбранный Python;
- `garak_runner` получает custom/system Python через переменные;
- `langchain_runtime` использует уже выбранный `llm_selected_python_binary`.

---

# Ollama

В проекте `Ollama` разворачивается как Docker-контейнер, а не как systemd-service или ручная установка в хостовую систему.

Роли:

- `ollama_container` — поднимает контейнер;
- `ollama_pull_models` — синхронизирует список моделей.

Базовые пути:

```bash
/opt/llm/ollama
/opt/llm/ollama/compose
/opt/llm/ollama/data
/opt/llm/ollama/compose/compose.yml
```

Основные параметры:

- контейнер: `ollama`;
- образ: `ollama/ollama:latest`;
- Docker network: `llm_stack_net`;
- bind address: `0.0.0.0`;
- host port: `11434`;
- internal port: `11434`;
- restart policy: `unless-stopped`.

Данные и модели Ollama хранятся на хосте:

```bash
/opt/llm/ollama/data
```

Проверка контейнера:

```bash
docker ps | grep ollama
docker inspect -f '{{.State.Running}}' ollama
```

Проверка API:

```bash
curl http://127.0.0.1:11434/api/tags
```

Проверка списка моделей:

```bash
docker exec ollama ollama list
```

Ручная загрузка модели:

```bash
docker exec ollama ollama pull qwen2.5:14b
docker exec ollama ollama pull nomic-embed-text:latest
```

На `urfu-server` сейчас используются модели:

```yaml
rag_agent_chat_model: "qwen2.5:14b"
rag_agent_embedding_model: "nomic-embed-text:latest"
```

И список моделей переопределяется так:

```yaml
ollama_pull_models_list:
  - "{{ rag_agent_chat_model }}"
  - "{{ rag_agent_embedding_model }}"
  - smollm:135m
```

---

# RAG-agent

`RAG-agent` — это backend-сервис, который разворачивается отдельной ролью `rag_agent`.

Роль делает следующее:

- проверяет Docker CLI и Docker daemon;
- устанавливает `git`, если он нужен для clone;
- создает каталоги;
- клонирует репозиторий `g1nry/rag_agent`;
- накладывает overlay-патчи для Langfuse;
- добавляет зависимость `langfuse>=3,<4` в `pyproject.toml`;
- собирает Docker-образ `rag-agent:local`;
- шаблонизирует compose-файл;
- запускает контейнер `rag-agent`;
- проверяет endpoint `/health`.

Базовые пути:

```bash
/opt/llm/rag-agent
/opt/llm/rag-agent/src
/opt/llm/rag-agent/compose
/opt/llm/rag-agent/data
/opt/llm/rag-agent/data/documents
/opt/llm/rag-agent/data/indexes
```

Основные параметры:

- контейнер: `rag-agent`;
- образ: `rag-agent:local`;
- порт: `8000`;
- Docker network: `llm_stack_net`;
- подключение к Ollama: `http://ollama:11434`;
- подключение к Langfuse: `http://langfuse-web:3000`.

Compose-файл прокидывает в контейнер env-переменные:

```text
APP_PORT
APP_HOST
OLLAMA_BASE_URL
NEMO_GUARDRAILS_OLLAMA_URL
OLLAMA_CHAT_MODEL
OLLAMA_EMBEDDING_MODEL
OLLAMA_TIMEOUT
MAX_CHUNK_SIZE
CHUNK_OVERLAP
DEFAULT_TOP_K
MIN_RETRIEVAL_SCORE
MAX_UPLOAD_SIZE_BYTES
ALLOWED_DOCUMENT_EXTENSIONS
UI_ENABLED
LANGFUSE_BASE_URL
LANGFUSE_HOST
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY
LANGFUSE_TRACING_ENABLED
```

Важный момент: Ansible не редактирует внешний репозиторий RAG-agent руками навсегда. Он каждый раз после `git clone` накладывает overlay-патч перед Docker build.

Langfuse overlay делает 2 вида трейсинга:

- `/api/v1/chat` и `/api/agent/chat`:
  - трейсятся через LangChain/LangGraph callback;
  - trace name: `rag-agent-chat`;
  - tags: `rag-agent`, `agent-chat`.

- `/api/v1/rag/chat`:
  - трейсится через `@observe` и manual observations;
  - trace name: `rag-chat`;
  - tags: `rag-agent`, `rag-chat`;
  - внутри trace есть `rag-retrieval` и `rag-ollama-generate`.

Проверка RAG-agent:

```bash
docker ps | grep rag-agent
curl -i http://127.0.0.1:8000/health
docker logs --tail=100 rag-agent
```

Ожидаемый health:

```json
{"status":"ok","agent_initialized":true}
```

Проверка переменных Langfuse внутри контейнера:

```bash
docker exec rag-agent env | grep LANGFUSE
```

Проверка SDK и auth:

```bash
docker exec rag-agent python -c \
  "from langfuse import get_client; print(get_client().auth_check())"
```

Ожидаемый результат:

```text
True
```

---

# Open WebUI с Nemo Guardrails

Старая роль `ollama_webui` больше не используется.

Вместо неё проект использует роль:

```text
open_webui_guardrails
```

Эта роль разворачивает Open WebUI с доустановленными Nemo Guardrails.

Что делает роль:

- клонирует репозиторий `phenkka/newWebLLM`;
- собирает локальный Docker-образ `open-webui-guardrails:local`;
- использует `Dockerfile.guardrails`;
- прокидывает настройки Ollama;
- прокидывает настройки Nemo Guardrails;
- запускает контейнер `open-webui`;
- проверяет HTTP-доступность.

Основные параметры:

- контейнер: `open-webui`;
- образ: `open-webui-guardrails:local`;
- внешний порт: `3030`;
- внутренний порт: `8080`;
- Docker network: `llm_stack_net`;
- путь: `/opt/llm/open-webui`.

Пути:

```bash
/opt/llm/open-webui
/opt/llm/open-webui/src
/opt/llm/open-webui/compose
/opt/llm/open-webui/data
```

Проверка:

```bash
docker ps | grep open-webui
curl -I http://127.0.0.1:3030/
docker logs --tail=100 open-webui
```

Доступ в браузере:

```text
http://<host>:3030
```

Для `urfu-server`:

```text
http://10.40.240.103:3030
```

Важно: чаты Open WebUI сейчас не отправляются в Langfuse напрямую. Open WebUI подключен к Ollama и Nemo Guardrails, но Langfuse-интеграция для Open WebUI отложена как отдельный этап. Сейчас Langfuse покрывает RAG-agent.

---

# Langfuse

`Langfuse` используется в проекте как self-hosted LLM-observability платформа.

Он нужен не для мониторинга контейнеров, CPU или GPU. Это делает Prometheus + Grafana.

Langfuse нужен для того, чтобы смотреть, что происходит внутри LLM-приложения:

- какой запрос пришёл;
- какой prompt был отправлен в модель;
- какая модель отвечала;
- какой ответ вернулся;
- сколько длился вызов;
- какие шаги сделал агент;
- какие документы достал RAG;
- где возникла ошибка;
- какие session_id и tags были у запроса.

В проекте Langfuse разворачивается ролью:

```text
langfuse_stack
```

Роль поднимает Langfuse v3 в Docker Compose:

- `langfuse-web` — UI и API;
- `langfuse-worker` — обработка ingestion-событий;
- `langfuse-postgres` — пользователи, проекты, настройки;
- `langfuse-clickhouse` — traces, observations, scores;
- `langfuse-redis` — очередь;
- `langfuse-minio` — S3-совместимое хранилище сырых событий.

Базовые пути:

```bash
/opt/llm/langfuse
/opt/llm/langfuse/compose
/opt/llm/langfuse/compose/compose.yml
/opt/llm/langfuse/compose/langfuse.env
```

`langfuse.env` содержит секреты и создается с правами `0600`.

Порты:

```text
host: 3001
container: 3000
```

Внешний URL:

```text
http://<host>:3001
```

Для `urfu-server`:

```text
http://10.40.240.103:3001
```

Внутренний URL для RAG-agent:

```text
http://langfuse-web:3000
```

Почему используется порт `3001`:

- `3000` уже занят Grafana;
- `3030` занят Open WebUI;
- `9090` занят Prometheus.

## Что создаётся при первом старте

Langfuse bootstrap-переменные создают:

- организацию;
- проект;
- пользователя;
- project public key;
- project secret key.

В текущем стенде ожидаемые логические имена:

```text
Organization: LLM Polygon
Project: rag-agent
```

Сами секретные значения в README не фиксируются.

## Запуск Langfuse

```bash
ansible-playbook site.yml --tags langfuse
```

Проверка контейнеров:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'langfuse|postgres|clickhouse|redis|minio'
```

Ожидаемые контейнеры:

```text
langfuse-web
langfuse-worker
langfuse-postgres
langfuse-clickhouse
langfuse-redis
langfuse-minio
```

Проверка health:

```bash
curl -i http://127.0.0.1:3001/api/public/health
curl -i http://127.0.0.1:3001/api/public/ready
```

Ожидаемый результат:

```text
HTTP/1.1 200 OK
```

Проверка UI:

```bash
curl -I http://127.0.0.1:3001/
```

Проверка из браузера:

```text
http://10.40.240.103:3001
```

Проверка, что `langfuse-web` находится в нужных сетях:

```bash
docker inspect langfuse-web --format '{{json .NetworkSettings.Networks}}' | python3 -m json.tool
```

Должны быть сети:

```text
langfuse_internal
llm_stack_net
```

Проверка доступа к Langfuse из общей Docker-сети:

```bash
docker run --rm --network llm_stack_net curlimages/curl:latest \
  -i http://langfuse-web:3000/api/public/health
```

---

# Langfuse smoke-test

Этот раздел нужен для быстрой проверки, что Langfuse и RAG-agent связаны правильно.

Порядок проверки:

```bash
ansible-playbook site.yml --tags langfuse
ansible-playbook site.yml --tags rag_agent
```

Проверить контейнеры:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'langfuse|rag-agent'
```

Проверить health:

```bash
curl -i http://localhost:3001/api/public/health
curl -i http://localhost:8000/health
```

Проверить, что RAG-agent получил Langfuse-переменные:

```bash
docker exec rag-agent env | grep LANGFUSE
```

Ожидаемо должны быть переменные:

```text
LANGFUSE_BASE_URL=http://langfuse-web:3000
LANGFUSE_HOST=http://langfuse-web:3000
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_TRACING_ENABLED=true
```

Проверить `auth_check`:

```bash
docker exec rag-agent python -c \
  "from langfuse import get_client; print('auth_check:', get_client().auth_check())"
```

Ожидаемо:

```text
auth_check: True
```

## Проверка `/api/v1/chat`

Этот endpoint идет через agent/LangGraph путь.

Запрос:

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Тест agent trace","thread_id":"agent-smoke-final"}'
```

Что должно появиться в Langfuse:

```text
Project rag-agent -> Tracing -> Traces -> rag-agent-chat
```

Ожидаемые признаки trace:

- name: `rag-agent-chat`;
- session: `agent-smoke-final`;
- tags: `rag-agent`, `agent-chat`;
- внутри видно LangGraph flow;
- внутри видно `ChatOllama`;
- видны prompt/completion tokens, если их отдала модель/интеграция.

## Проверка `/api/v1/rag/chat`

Этот endpoint идет через обычный RAG-путь.

Если документов ещё нет, сначала загрузить тестовый документ:

```bash
printf 'Полигон URFU использует Ollama, RAG-agent, LangGraph и Langfuse для наблюдаемости LLM-приложений.' > /tmp/langfuse_rag_test.txt

curl -s -X POST http://localhost:8000/api/v1/documents/upload \
  -F 'file=@/tmp/langfuse_rag_test.txt'
```

Потом отправить RAG-запрос:

```bash
curl -s -X POST http://localhost:8000/api/v1/rag/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Что использует полигон URFU?","thread_id":"rag-smoke-final","top_k":4}'
```

Что должно появиться в Langfuse:

```text
Project rag-agent -> Tracing -> Traces -> rag-chat
```

Ожидаемые признаки trace:

- name: `rag-chat`;
- session: `rag-smoke-final`;
- tags: `rag-agent`, `rag-chat`;
- внутри есть observation `rag-retrieval`;
- внутри есть generation `rag-ollama-generate`;
- в `rag-retrieval` видно количество найденных контекстов и preview текста;
- в `rag-ollama-generate` видно prompt и ответ модели.

Итог успешной проверки:

```text
/api/v1/chat      -> trace rag-agent-chat
/api/v1/rag/chat  -> trace rag-chat
```

---

# Проверка идемпотентности

Идемпотентность означает, что повторный запуск playbook поверх уже работающего стенда не ломает сервисы и не дублирует патчи.

Для проверки ничего сносить не нужно.

Повторный прогон:

```bash
ansible-playbook site.yml --tags langfuse
ansible-playbook site.yml --tags rag_agent
```

После этого проверить health:

```bash
curl -i http://localhost:3001/api/public/health
curl -i http://localhost:8000/health
```

Проверить контейнеры:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'langfuse|rag-agent'
```

Проверить, что импорты не задублировались:

```bash
grep -n "from ..core.observability import langchain_config" \
  /opt/llm/rag-agent/src/src/rag_agent/agents/main_agent.py
```

Должна быть одна строка.

Проверить, что декоратор direct RAG не задублировался:

```bash
grep -n '@observe(name="rag-chat")' \
  /opt/llm/rag-agent/src/src/rag_agent/main.py
```

Должна быть одна строка.

Проверить RAG observations:

```bash
grep -n 'rag-retrieval\|rag-ollama-generate' \
  /opt/llm/rag-agent/src/src/rag_agent/main.py
```

Должны быть оба блока.

Проверить новые traces:

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Проверка идемпотентности agent trace","thread_id":"agent-idempotency-1"}'

curl -s -X POST http://localhost:8000/api/v1/rag/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Что использует полигон URFU?","thread_id":"rag-idempotency-1","top_k":4}'
```

В Langfuse должны появиться новые traces:

```text
rag-agent-chat
rag-chat
```

---

# Monitoring

Проект разворачивает monitoring stack через Docker Compose.

В текущем виде используются:

- Prometheus;
- Grafana;
- node-exporter;
- cAdvisor.

Базовый каталог:

```bash
/opt/llm/monitoring
```

Основные порты:

```text
Prometheus:    9090
Grafana:       3000
node-exporter: 9100
cAdvisor:      8081
```

Проверить контейнеры:

```bash
docker ps | grep -E 'prometheus|grafana|node-exporter|cadvisor'
```

Проверка Prometheus:

```bash
curl http://127.0.0.1:9090/-/ready
```

Проверка Grafana:

```bash
curl -I http://127.0.0.1:3000
```

Основные файлы monitoring stack:

```bash
/opt/llm/monitoring/compose/compose.yml
/opt/llm/monitoring/compose/prometheus.yml
/opt/llm/monitoring/grafana-provisioning
```

Если monitoring уже развернут, для перезапуска можно использовать:

```bash
cd /opt/llm/monitoring/compose
docker compose restart
```

Если нужно пересоздать stack:

```bash
cd /opt/llm/monitoring/compose
docker compose down
docker compose up -d
```

---

# Garak

Garak в проекте ставится в отдельный venv, а не в системный Python напрямую.

Роль:

```text
garak_runner
```

Что делает роль:

- выбирает Python для Garak через общую Python strategy проекта;
- создает отдельный `venv`;
- устанавливает `garak`;
- проверяет `garak --help`;
- создает helper-скрипт для ручного запуска против Ollama.

Основные пути:

```bash
/opt/llm/garak
/opt/llm/garak/venv
/opt/llm/garak/reports
/opt/llm/garak/bin
/opt/llm/garak/bin/run_garak_ollama.sh
```

Версия Garak в проекте сейчас зафиксирована:

```bash
garak==0.14.0
```

В сценарии `urfu-server` Garak временно отключен:

```yaml
garak_runner_enable: false
```

Причина: была проблема с установкой `garak==0.14.0` и зависимостью `mistralai==1.5.2`.

Если Garak включен и установлен, проверка такая:

```bash
/opt/llm/garak/venv/bin/garak --help
```

Helper-скрипт:

```bash
/opt/llm/garak/bin/run_garak_ollama.sh
```

Примеры запуска:

```bash
/opt/llm/garak/bin/run_garak_ollama.sh
/opt/llm/garak/bin/run_garak_ollama.sh qwen2.5:7b
/opt/llm/garak/bin/run_garak_ollama.sh llama3.1:8b
```

Отчеты:

```bash
/opt/llm/garak/reports
```

---

# LangChain runtime

`LangChain` в проекте ставится в отдельный `venv`, а не в системный Python напрямую.

Роль:

```text
langchain_runtime
```

Что делает роль:

- проверяет выбранный Python;
- создает родительский каталог для `venv`;
- создает отдельный `venv`;
- обновляет `pip`, `setuptools`, `wheel`;
- устанавливает LangChain-стек;
- проверяет импорты.

Основной путь:

```bash
/opt/venvs/langchain311
```

Пакеты по умолчанию:

```yaml
langchain_runtime_packages:
  - langchain
  - langchain-community
  - langgraph
```

Проверка:

```bash
/opt/venvs/langchain311/bin/python -c "import langchain; import langchain_community; import langgraph; print('langchain stack import ok')"
```

---

# Platform users

Роль `platform_users` отвечает за создание и настройку пользователей платформы.

Что делает роль:

- проверяет, что `platform_users_list` задан и не пустой;
- проверяет наличие системных групп `docker` и `sudo`;
- при необходимости создает общую группу команды;
- создает пользователей с домашними каталогами;
- добавляет пользователей в нужные группы;
- при необходимости создает общий каталог для совместной работы.

Базовые дополнительные группы для пользователей:

```yaml
platform_users_default_groups:
  - sudo
  - docker
```

Общая группа команды:

```yaml
platform_users_shared_group_name: llm-admins
```

Общий каталог:

```bash
/opt/llm/shared
```

Режим каталога:

```text
2775
```

`2775` нужен для `setgid`, чтобы новые файлы наследовали групповую принадлежность каталога.

Проверка:

```bash
getent group sudo
getent group docker
getent group llm-admins
id Alex
ls -ld /opt/llm/shared
```

Важно: роль ожидает hash пароля, а не открытый пароль. Значения вида `REPLACE_ME` нужно заменить перед реальным использованием.

---

# Секреты и Vault

В текущей версии проекта Ansible Vault пока не используется полноценно.

Часть чувствительных значений сейчас временно лежит в `group_vars/urfu-server.yml`.

Это допустимо для лабораторного стенда, но не является правильным финальным вариантом.

К чувствительным значениям относятся:

- `open_webui_secret_key`;
- `langfuse_encryption_key`;
- `langfuse_nextauth_secret`;
- `langfuse_salt`;
- `langfuse_postgres_password`;
- `langfuse_clickhouse_password`;
- `langfuse_redis_auth`;
- `langfuse_minio_root_password`;
- `langfuse_init_user_password`;
- `langfuse_init_project_secret_key`;
- `monitoring_stack_grafana_admin_password`;
- password hashes пользователей из `platform_users_list`.

Важно: во время тестирования часть Langfuse-секретов была засвечена в логах/скриншотах. Перед финальной публикацией проекта, передачей отчета или использованием стенда как постоянного окружения эти значения нужно ротировать.

Что нужно сделать перед финальным состоянием:

1. Пересоздать Langfuse project API keys.
2. Перегенерировать временные Langfuse-секреты.
3. Обновить значения в переменных.
4. Перезапустить `langfuse_stack` и `rag_agent`.
5. Вынести секреты в Ansible Vault.

Генерация `ENCRYPTION_KEY`:

```bash
openssl rand -hex 32
```

Он должен быть ровно 64 hex-символа.

Пример создания Vault-файла:

```bash
ansible-vault create group_vars/urfu-server-secrets.yml
```

Пример редактирования:

```bash
ansible-vault edit group_vars/urfu-server-secrets.yml
```

Пример запуска playbook с Vault:

```bash
ansible-playbook site.yml --ask-vault-pass
```

Возможная структура в будущем:

```text
group_vars/
├── all.yml
├── urfu-server.yml
├── urfu-server-secrets.yml
├── cpu_only.yml
├── cloud_gpu_install.yml
├── cloud_gpu_ready.yml
└── wsl2_gpu.yml
```

В таком варианте:

- обычные переменные остаются в `group_vars/*.yml`;
- чувствительные значения переезжают в `urfu-server-secrets.yml`;
- запуск выполняется с `--ask-vault-pass`.

---

# Проверки после установки

После выполнения playbook проверь, что в `PLAY RECAP` нет `failed`.

Минимальный чек-лист:

```bash
docker version
docker info
```

```bash
docker ps
```

```bash
curl http://127.0.0.1:11434/api/tags
```

```bash
curl -i http://127.0.0.1:8000/health
```

```bash
curl -I http://127.0.0.1:3030/
```

```bash
curl -i http://127.0.0.1:3001/api/public/health
```

```bash
curl http://127.0.0.1:9090/-/ready
```

```bash
curl -I http://127.0.0.1:3000
```

Проверка моделей:

```bash
docker exec ollama ollama list
```

Проверка Langfuse auth из RAG-agent:

```bash
docker exec rag-agent python -c \
  "from langfuse import get_client; print(get_client().auth_check())"
```

Проверка traces:

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Тест agent trace","thread_id":"agent-readme-check"}'
```

```bash
curl -s -X POST http://localhost:8000/api/v1/rag/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Что использует полигон URFU?","thread_id":"rag-readme-check","top_k":4}'
```

Потом открыть:

```text
http://10.40.240.103:3001
```

И перейти:

```text
Project rag-agent -> Tracing -> Traces
```

---

# Типичные проблемы

## Langfuse UI не открывается

**Симптомы**

```bash
curl -I http://127.0.0.1:3001
```

возвращает ошибку, timeout или connection reset.

**Что проверить**

```bash
docker ps | grep langfuse
docker logs --tail=150 langfuse-web
sudo ss -lntp | grep ':3001'
```

Проверить, что в compose у `langfuse-web` есть:

```yaml
environment:
  HOSTNAME: "0.0.0.0"
  PORT: "3000"
ports:
  - "0.0.0.0:3001:3000"
```

## Langfuse ready долго не становится 200

**Симптомы**

```bash
curl -i http://127.0.0.1:3001/api/public/ready
```

возвращает `503` или не отвечает.

**Что проверить**

```bash
docker logs --tail=120 langfuse-web
docker logs --tail=120 langfuse-worker
docker logs --tail=120 langfuse-clickhouse
docker logs --tail=120 langfuse-postgres
```

Чаще всего причина:

- ClickHouse ещё инициализируется;
- миграции ещё применяются;
- не хватает RAM;
- Redis/MinIO/Postgres unhealthy.

## RAG-agent не стартует после overlay-патча

**Симптомы**

```bash
docker logs rag-agent
```

показывает `SyntaxError`, `ImportError` или `ModuleNotFoundError`.

**Что проверить**

```bash
docker logs --tail=150 rag-agent
sed -n '55,90p' /opt/llm/rag-agent/src/src/rag_agent/agents/main_agent.py
sed -n '190,280p' /opt/llm/rag-agent/src/src/rag_agent/main.py
```

Если сломан локальный image, можно пересобрать чисто, не трогая data:

```bash
sudo docker compose -f /opt/llm/rag-agent/compose/compose.yml down 2>/dev/null || true
sudo docker rm -f rag-agent 2>/dev/null || true
sudo docker image rm rag-agent:local 2>/dev/null || true
sudo rm -rf /opt/llm/rag-agent/src
```

Потом:

```bash
ansible-playbook site.yml --tags rag_agent
```

## В Langfuse нет traces

**Симптомы**

RAG-agent отвечает, но в Langfuse UI пусто.

**Что проверить**

```bash
docker exec rag-agent env | grep LANGFUSE
```

```bash
docker exec rag-agent python -c \
  "from langfuse import get_client; print(get_client().auth_check())"
```

```bash
docker exec rag-agent python -c \
  "import urllib.request; print(urllib.request.urlopen('http://langfuse-web:3000/api/public/health').status)"
```

Если `auth_check: False`, значит ключи в RAG-agent не совпадают с ключами проекта Langfuse.

Если нет доступа к `langfuse-web`, значит проблема в Docker network.

## Open WebUI открывается, но не работает с моделями

**Симптомы**

Web UI открывается, но список моделей пустой или запросы к модели завершаются ошибкой.

**Что проверить**

```bash
docker ps | grep ollama
docker ps | grep open-webui
curl http://127.0.0.1:11434/api/tags
docker logs --tail=100 ollama
docker logs --tail=100 open-webui
```

Также проверить, что оба контейнера находятся в сети `llm_stack_net`.

## Garak не ставится

**Симптомы**

Роль `garak_runner` падает на установке зависимостей.

**Что проверить**

```bash
/opt/python311/bin/python3.11 --version
/usr/bin/python3 --version
```

В текущем `urfu-server` Garak временно отключен:

```yaml
garak_runner_enable: false
```

Если нужно снова включить Garak, лучше отдельно проверить совместимые версии Python и зависимостей.

---

# Что пока отложено

- Подключение Open WebUI к Langfuse.

Сейчас Langfuse покрывает RAG-agent:

```text
/api/v1/chat
/api/v1/rag/chat
```

Но не покрывает чаты, которые пользователь ведёт напрямую через Open WebUI.

Это можно сделать отдельным этапом, но не стоит смешивать с текущей интеграцией. Предпочтительный путь на будущее — изучить вариант через Open WebUI Filter Functions, а не старые Pipelines.

- Полный перенос секретов в Ansible Vault.

Сейчас часть секретов временно лежит в `group_vars/urfu-server.yml`. Перед финальной публикацией проекта нужно ротировать засвеченные значения и вынести их в Vault.

- Полное обновление Garak runner.

В `urfu-server` Garak временно отключен из-за проблем с установкой старой версии и зависимостями.

---

# Минимальный итог

После успешного развёртывания на `urfu-server` должны работать:

```text
Ollama API       http://10.40.240.103:11434
RAG-agent        http://10.40.240.103:8000
Open WebUI       http://10.40.240.103:3030
Langfuse         http://10.40.240.103:3001
Prometheus       http://10.40.240.103:9090
Grafana          http://10.40.240.103:3000
node-exporter    http://10.40.240.103:9100
cAdvisor         http://10.40.240.103:8081
```

Главная проверка LLM-observability:

```text
Langfuse UI -> Project rag-agent -> Tracing -> Traces
```

Там должны появляться:

```text
rag-agent-chat   для /api/v1/chat
rag-chat         для /api/v1/rag/chat
```
