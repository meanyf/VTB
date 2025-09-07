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