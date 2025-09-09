# Запуск проекта

## 1. Запуск базы данных
```bash
docker-compose -f docker-compose.yml up -d postgres2
```

## 2. Запуск без Docker
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload

```

## 3. Запуск через Docker. Перейдите по адресу localhost:8002
```bash
docker-compose -f docker-compose.yml build app
docker-compose -f docker-compose.yml run --rm --service-ports app
```


## 4. Очистка ресурсов
```bash
# Удалить БД
docker-compose -f docker-compose.yml stop postgres2
docker-compose -f docker-compose.yml rm -f postgres2
docker volume rm vtb-2_postgres_data2

# Удалить приложение
docker-compose -f docker-compose.yml stop app
docker-compose -f docker-compose.yml rm -f app

# Удалить образ
docker rmi vtb-python-app
```