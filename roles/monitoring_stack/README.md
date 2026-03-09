# monitoring_stack

## Назначение

Роль для развертывания базового monitoring stack на Docker-хосте.

## Что делает

- проверяет доступность Docker;
- создает каталоги под мониторинг;
- создает Docker network при необходимости;
- шаблонит конфиг Prometheus;
- шаблонит docker compose файл;
- запускает Prometheus, Grafana, Node Exporter и cAdvisor;
- проверяет доступность Prometheus и Grafana.

## Что не делает

- не импортирует готовые dashboard в Grafana;
- не настраивает alertmanager;
- не создает отдельных exporter для Ollama.

Это можно добавить позже отдельными ролями или расширением этой роли.