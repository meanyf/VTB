# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем необходимые пакеты для компиляции psutil
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev  # Если нужно для psycopg2
    
# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Указываем команду, которая будет запускаться при старте контейнера
CMD ["python", "app/main.py"]
