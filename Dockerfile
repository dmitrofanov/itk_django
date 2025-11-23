FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование скрипта ожидания базы данных
COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

# Копирование проекта
COPY . .

# Создание директории для статики
RUN mkdir -p /app/staticfiles

# Команда по умолчанию (будет переопределена в docker-compose.yml)
# Для development используем runserver, для production - gunicorn
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


