import psycopg
from explain_analyze import run_explain
from stats_analysis import analyze_stats
from DB_tuning import get_postgres_recommendations
from find_N import analyze_n_plus_one
from index_recommend import analyze_indexes  # <-- импорт


def get_db_connection():
    return psycopg.connect(
        host="localhost",
        port="5434",
        dbname="pagila",
        user="readonly_user",
        password="readonly_password",
    )


def menu():
    conn = get_db_connection()

    while True:
        print("\nМеню:")
        print("1. Запуск EXPLAIN ANALYZE для запроса")
        print("2. Анализ статистики запросов и рекомендации для autovacuum")
        print("3. Рекомендации по настройкам PostgreSQL")
        print("4. Поиск N+1 кандидатов (pg_stat_statements)")
        print("5. Рекомендации по индексам")  # <-- новый пункт
        print("6. Выход")

        choice = input("Выберите опцию: ")

        if choice == "1":
            query = input("Введите SQL запрос: ")
            run_explain(query, conn)
        elif choice == "2":
            query = input("Введите SQL запрос: ")
            analyze_stats(query, conn)
        elif choice == "3":
            get_postgres_recommendations(conn)
        elif choice == "4":
            analyze_n_plus_one(conn)
        elif choice == "5":
            query = input("Введите SQL запрос: ")
            analyze_indexes(query, conn)  # <-- вызов новой функции
        elif choice == "6":
            print("Выход из программы...")
            break
        else:
            print("Неверный выбор, попробуйте снова.")

    conn.close()


if __name__ == "__main__":
    menu()
