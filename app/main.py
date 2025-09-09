from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import psycopg
import time
import os
import socket
import asyncio
import logging

# Импортируем ваши функции анализа
from app.explain_analyze import run_explain
from app.stats_analysis import analyze_stats
from app.DB_tuning import get_postgres_recommendations
from app.find_N import analyze_n_plus_one
from app.index_recommend import analyze_indexes

# --- Наст
# --- Настройки логгера ---
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- FastAPI setup ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Модели ---
class QueryRequest(BaseModel):
    query: str


class DbParams(BaseModel):
    host: str
    port: str
    dbname: str
    user: str
    password: str


# --- Глобальные переменные ---
in_docker = bool(os.getenv("DATABASE_URL"))
user_dict = {}
db_choice = ""


# --- Утилиты ---
def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def get_db_connection(max_retries=10, delay=2, connect_timeout=3):
    """
    Синхронная функция. Возвращает подключение или бросает исключение.
    - time.sleep (синхронная задержка)
    - различает фатальные (auth) и временные ошибки
    """
    global user_dict, db_choice

    if user_dict and db_choice == "custom":
        host = user_dict.get("host")
        if in_docker and host and host.lower() == "localhost":
            host = "host.docker.internal"
        port = int(user_dict.get("port", 5432))
        dbname = user_dict.get("dbname")
        user = user_dict.get("user")
        password = user_dict.get("password")
        max_attempts = min(max_retries, 3)  # меньше попыток для кастомных
    else:
        host = "postgres2" if in_docker else "127.0.0.1"
        port = 5432 if in_docker else 5434
        dbname = "pagila"
        user = "readonly_user"
        password = "readonly_password"
        max_attempts = max_retries

    logger.debug(f"Подключение к {host}:{port}/{dbname} (до {max_attempts} попыток)")

    for attempt in range(1, max_attempts + 1):
        if not is_port_open(host, port, timeout=1.0):
            logger.debug(
                f"Попытка {attempt}: TCP {host}:{port} недоступен — жду {delay}s"
            )
            time.sleep(delay)
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
            logger.info(f"Успешное подключение к {host}:{port}/{dbname}")
            return conn
        except Exception as e:
            msg = str(e).lower()
            logger.warning(f"Попытка {attempt}: ошибка подключения: {e}")

            # Если это auth-ошибка → прекращаем повторы
            auth_indicators = [
                "password authentication failed",
                "authentication failed",
                "no password supplied",
                "role",
                "invalid password",
                "fatal",
            ]
            if any(ind in msg for ind in auth_indicators):
                logger.error("Фатальная ошибка подключения (auth). Прекращаю повторы.")
                raise RuntimeError(f"Permanent connection failure: {e}") from e

            if attempt < max_attempts:
                time.sleep(delay)
                continue
            else:
                break

    raise RuntimeError(f"Не удалось подключиться к базе после {max_attempts} попыток")


# --- Эндпоинты ---
@app.post("/save_db_choice/")
async def save_db_choice(db_choice_data: dict):
    global db_choice
    try:
        db_choice = db_choice_data.get("db_choice", "")
        logger.info(f"Сохранено состояние dbChoice: {db_choice}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        conn = await asyncio.to_thread(get_db_connection)
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        raise HTTPException(status_code=500, detail="DB connection failed")
    else:
        conn.close()
        return templates.TemplateResponse("index.html", {"request": request})


@app.post("/save_db_params/")
async def save_db_params(db_params: DbParams):
    global user_dict
    try:
        user_dict = db_params.dict()
        # тестовое подключение (короткое)
        try:
            conn = await asyncio.to_thread(get_db_connection, 2, 1, 2)
        except Exception as e:
            user_dict = {}
            raise HTTPException(status_code=400, detail=f"Не удалось подключиться: {e}")
        else:
            conn.close()
            logger.info("Параметры сохранены и протестированы")
            return {"success": True, "saved_db_params": db_params.dict()}
    except HTTPException:
        raise
    except Exception as e:
        user_dict = {}
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении: {str(e)}")


@app.post("/run_explain/")
async def run_explain_api(request: QueryRequest):
    try:
        conn = await asyncio.to_thread(get_db_connection)
        result = run_explain(request.query, conn)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.post("/analyze_stats/")
async def analyze_stats_api():
    try:
        conn = await asyncio.to_thread(get_db_connection)
        result = analyze_stats(conn)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.post("/get_postgres_recommendations/")
async def get_postgres_recommendations_api():
    try:
        conn = await asyncio.to_thread(get_db_connection)
        result = get_postgres_recommendations(conn)
        return {"recommendations": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.post("/analyze_n_plus_one/")
async def analyze_n_plus_one_api():
    try:
        conn = await asyncio.to_thread(get_db_connection)
        result = analyze_n_plus_one(conn)
        return {"n_plus_one_candidates": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.post("/analyze_indexes/")
async def analyze_indexes_api(request: QueryRequest):
    try:
        conn = await asyncio.to_thread(get_db_connection)
        result = analyze_indexes(request.query, conn)
        return {"index_recommendations": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/exit/")
async def exit_program():
    logger.info("Выход из программы...")
    return {"message": "Exiting program..."}
