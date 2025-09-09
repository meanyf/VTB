from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Подключение к базе данных и другие необходимые импорты
import psycopg
import time
import os

# Импортируем функции для анализа
from app.explain_analyze import run_explain
from app.stats_analysis import analyze_stats
from app.DB_tuning import get_postgres_recommendations
from app.find_N import analyze_n_plus_one
from app.index_recommend import analyze_indexes

app = FastAPI()

# Настройка шаблонов и статичных файлов
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Модель для запроса
class QueryRequest(BaseModel):
    query: str


import psycopg
import time
import logging

# Настройка логгера
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
import logging
import psycopg
import time
import os

import logging
import psycopg
import time
import os
import logging
import psycopg
import time
import os
import socket
import asyncio

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        # быстрый проверочный TCP connect с малым таймаутом
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

in_docker = bool(os.getenv("DATABASE_URL"))
user_dict = {}
def get_db_connection(max_retries=60, delay=2, connect_timeout=3):
    # print(user_dict and db_choice == 'custom')
    if user_dict and db_choice == 'custom' :
        host = user_dict['host']
        if in_docker and host.lower() == "localhost":
            host = "host.docker.internal"
        port = user_dict['port']
        dbname = user_dict['dbname']
        user = user_dict['user']
        password = user_dict['password']
    else:
        host = "postgres2" if in_docker else "127.0.0.1"
        port = 5432 if in_docker else 5434
        dbname = "pagila"
        user = "readonly_user"
        password = "readonly_password"
    print(dbname)
    for attempt in range(1, max_retries + 1):
        if not is_port_open(host, port, timeout=1.0):
            print(
                f"Попытка {attempt}: tcp {host}:{port} недоступен — пропускаем попытку.",
                flush=True,
            )
            asyncio.sleep(delay)
            continue

        try:
            conn = psycopg.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                connect_timeout=connect_timeout,
            )
            return conn
        except Exception as e:
            print(f"Попытка {attempt}: Ошибка подключения: {e}", flush=True)
            asyncio.sleep(delay)

    raise RuntimeError("Подключение к базе данных не удалось.")

db_choice = ""


@app.post("/save_db_choice/")
async def save_db_choice(db_choice_data: dict):
    global db_choice
    try:
        # Извлекаем строку db_choice из переданных данных
        db_choice = db_choice_data.get("db_choice", "")
        print(f"Сохранено состояние dbChoice: {db_choice}")  # Для логирования
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        conn = await asyncio.to_thread(get_db_connection)
    except asyncio.CancelledError:
        print("Запрос прерван (shutdown).", flush=True)
        raise
    except Exception as e:
        print(f"Ошибка при подключении к БД: {e}", flush=True)
        raise HTTPException(status_code=500, detail="DB connection failed")
    else:
        conn.close()
        return templates.TemplateResponse("index.html", {"request": request})


# Модель для валидации параметров запроса
class DbParams(BaseModel):
    host: str
    port: str
    dbname: str
    user: str
    password: str

# Новый обработчик для сохранения параметров подключения и вывода их в ответ
@app.post("/save_db_params/")
async def save_db_params(db_params: DbParams):
    global user_dict  # Указываем, что мы используем глобальную переменную
    try:
        # Просто возвращаем полученные параметры
        print(db_params.dict())
        user_dict = db_params.dict()
        return {"success": True, "saved_db_params": db_params.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении: {str(e)}")


@app.post("/run_explain/")
async def run_explain_api(request: QueryRequest):
    conn = get_db_connection()
    try:
        query = request.query
        result = run_explain(query, conn)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze_stats/")
async def analyze_stats_api():
    conn = get_db_connection()
    try:
        result = analyze_stats(conn)
        print("FEFEFEFFE")
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get_postgres_recommendations/")
async def get_postgres_recommendations_api():
    conn = get_db_connection()
    try:
        result = get_postgres_recommendations(conn)
        return {"recommendations": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze_n_plus_one/")
async def analyze_n_plus_one_api():
    conn = get_db_connection()
    try:
        result = analyze_n_plus_one(conn)
        return {"n_plus_one_candidates": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze_indexes/")
async def analyze_indexes_api(request: QueryRequest):
    conn = get_db_connection()
    try:
        query = request.query
        result = analyze_indexes(query, conn)
        return {"index_recommendations": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/exit/")
async def exit_program():
    print("Выход из программы...")
    return {"message": "Exiting program..."}
