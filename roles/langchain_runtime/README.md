# langchain_runtime

Роль для создания отдельного Python virtual environment и установки LangChain-стека.

## Что делает роль

- создает отдельный `venv` на Python 3.11;
- обновляет `pip`, `setuptools`, `wheel`;
- устанавливает:
  - `langchain`
  - `langchain-community`
  - `langgraph`

## Предварительное условие

До запуска этой роли на хосте уже должен быть установлен Python 3.11, например ролью `python_runtime`.

## Пример запуска

```bash
ansible-playbook site.yml --tags langchain_runtime -K

## Пример запуска

```bash
/opt/venvs/langchain311/bin/python -c "import langchain; import langchain_community; import langgraph; print('ok')"