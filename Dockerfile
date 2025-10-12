# Базовый образ с Python 3.11
FROM python:3.11-slim

# Устанавливаем зависимости системы (если нужны)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию
WORKDIR /app

# Копируем только requirements сначала для кэширования
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Устанавливаем переменные окружения (опционально)
ENV PYTHONUNBUFFERED=1

# Команда запуска проекта
CMD ["python", "main.py"]
