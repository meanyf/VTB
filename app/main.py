import psycopg
from explain_analyze import run_explain
from stats_analysis import analyze_stats
from DB_tuning import get_postgres_recommendations
from find_N import analyze_n_plus_one
from index_recommend import analyze_indexes  # <-- импорт
import os

import time
import psycopg

import os
import time
import psycopg


import os
import time
import psycopg

def get_db_connection(max_retries=60, delay=2):
    # Надежное определение — находимся ли мы внутри Docker-контейнера
    in_docker = True if os.getenv("DATABASE_URL") else False

    use_custom = (
        input("Хотите ввести свои данные для подключения? (y/n) [n]: ").strip().lower() == "y"
    )

    # Значения по умолчанию в зависимости от среды
    host_default = "postgres2" if in_docker else "localhost"
    port_default = "5432" if in_docker else "5434"
    dbname_default = "pagila"
    user_default = "readonly_user"
    password_default = "readonly_password"

    if use_custom:
        print("\nВведите параметры подключения к базе данных.")
        print("Просто нажмите Enter, чтобы использовать значение по умолчанию, указанное в []:\n")

        host_input = input(f"Введите host [{host_default}]: ").strip() or host_default

        # Если в докере и ввели localhost, заменяем на host.docker.internal (локальный хост машины)
        if in_docker and host_input.lower() == "localhost":
            host = "host.docker.internal"
            print("ℹ️ 'localhost' в Docker заменён на 'host.docker.internal'")
        else:
            # Для удалённого сервера или любого другого хоста используем как есть
            host = host_input
        print(host)
        port = input(f"  ➤ Port [{port_default}]: ").strip() or port_default
        dbname = input(f"  ➤ Название базы данных [{dbname_default}]: ").strip() or dbname_default
        user = input(f"  ➤ Пользователь [{user_default}]: ").strip() or user_default
        password = input(f"  ➤ Пароль [{password_default}]: ").strip() or password_default
    else:
        host = host_default
        port = port_default
        dbname = dbname_default
        user = user_default
        password = password_default

    # Формируем строку подключения
    db_url = f"postgres://{user}:{password}@{host}:{port}/{dbname}"
    print(f"\n📡 Используем строку подключения: {db_url}\n")

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[{attempt}] Попытка подключения к базе данных...")
            conn = psycopg.connect(db_url)
            print("✅ Подключение успешно.")
            return conn

        except psycopg.OperationalError as e:
            print(f"⏳ Ошибка подключения: {e}")
            print(f"🔁 Повтор через {delay} секунд...\n")
            time.sleep(delay)

    print("❌ Не удалось подключиться к базе данных после нескольких попыток.")
    raise RuntimeError("Подключение к базе данных не удалось.")


def execute(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        print(f"❌ Ошибка при выполнении: {e}")


def menu():
    conn = get_db_connection()

    while True:
        print("\nМеню:")
        print("1. Запуск EXPLAIN ANALYZE для запроса")
        print("2. Анализ статистики запросов и рекомендации для autovacuum")
        print("3. Рекомендации по настройкам PostgreSQL")
        print("4. Поиск N+1 кандидатов (pg_stat_statements)")
        print("5. Рекомендации по индексам")
        print("6. Выход")

        choice = input("Выберите опцию: ")

        if choice == "1":
            query = input("Введите SQL запрос: ")
            execute(run_explain, query, conn)
        elif choice == "2":
            query = input("Введите SQL запрос: ")
            execute(analyze_stats, query, conn)
        elif choice == "3":
            execute(get_postgres_recommendations, conn)
        elif choice == "4":
            execute(analyze_n_plus_one, conn)
        elif choice == "5":
            query = input("Введите SQL запрос: ")
            execute(analyze_indexes, query, conn)
        elif choice == "6":
            print("Выход из программы...")
            break
        else:
            print("Неверный выбор, попробуйте снова.")

    conn.close()


if __name__ == "__main__":
    menu()
