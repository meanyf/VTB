# Используем более легкую версию Python (alpine)
FROM python:3.11-alpine

# Устанавливаем необходимые пакеты для компиляции зависимостей
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev make

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем переменную окружения для указания, что приложение работает на порту 8000
ENV HOST=0.0.0.0
ENV PORT=8002

# Запуск приложения через uvicorn, а не через python
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
