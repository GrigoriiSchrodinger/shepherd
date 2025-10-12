# Название виртуального окружения
VENV := venv
PYTHON := python3
PIP := pip3
REQ := requirements.txt

# Команда по умолчанию
.DEFAULT_GOAL := help

# 🧩 Создание виртуального окружения
$(VENV)/bin/activate:
	@echo ">>> Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo ">>> Virtual environment created."

# 📦 Установка зависимостей
install: $(VENV)/bin/activate
	@echo ">>> Installing dependencies..."
	$(VENV)/bin/$(PIP) install --upgrade pip
	$(VENV)/bin/$(PIP) install -r $(REQ)
	@echo ">>> Dependencies installed."

# 🚀 Запуск проекта
run: $(VENV)/bin/activate
	@echo ">>> Running project..."
	@. $(VENV)/bin/activate && $(PYTHON) main.py

# 🧹 Очистка окружения
clean:
	@echo ">>> Removing virtual environment..."
	rm -rf $(VENV)
	@echo ">>> Done."

# 🆙 Обновление зависимостей
update:
	@echo ">>> Updating dependencies..."
	@. $(VENV)/bin/activate && $(PIP) install --upgrade -r $(REQ)
	@echo ">>> Dependencies updated."

# 🆘 Справка
help:
	@echo ""
	@echo "Доступные команды:"
	@echo "  make install   - создать venv и установить зависимости"
	@echo "  make run       - запустить проект"
	@echo "  make update    - обновить зависимости"
	@echo "  make clean     - удалить venv"
	@echo ""
