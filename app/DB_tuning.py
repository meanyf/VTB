from psycopg import rows
import psutil
import json

PARAMS = ["shared_buffers", "effective_cache_size", "work_mem", "maintenance_work_mem"]


def recommend_postgres_settings(ram_gb: int, max_connections: int):
    ram_mb = ram_gb * 1024

    shared_buffers = int(ram_mb * 0.25)  # 25% от RAM
    effective_cache_size = int(ram_mb * 0.75)  # 75% от RAM
    work_mem = int(ram_mb * 0.25 / max_connections)  # на соединение
    maintenance_work_mem = min(int(ram_mb * 0.05), 1024)  # до 1 GB

    return {
        "shared_buffers": f"{shared_buffers}MB",
        "effective_cache_size": f"{effective_cache_size}MB",
        "work_mem": f"{work_mem}MB",
        "maintenance_work_mem": f"{maintenance_work_mem}MB",
    }


def get_postgres_recommendations(conn):
    cur = conn.cursor(row_factory=rows.dict_row)

    # Получаем max_connections
    cur.execute("SHOW max_connections;")
    max_connections_row = cur.fetchone()

    if max_connections_row is None:
        print("Ошибка: не удалось получить значение max_connections.")
        return

    max_connections = int(max_connections_row["max_connections"])

    # Получаем объем RAM на сервере
    total_ram_gb = round(psutil.virtual_memory().total / (1024**3))

    # Рекомендуемые настройки
    recommended = recommend_postgres_settings(total_ram_gb, max_connections)

    # Получаем текущие настройки в PostgreSQL
    current = {}
    for param in PARAMS:
        cur.execute(f"SHOW {param};")
        row = cur.fetchone()
        if row is not None and param in row:
            current[param] = row[param]

    print("PostgreSQL settings (current vs recommended):")
    result = {}
    for param in PARAMS:
        result[param] = {
            "current": current.get(param),
            "recommended": recommended.get(param),
        }

    print(json.dumps(result, indent=4))

    cur.close()
