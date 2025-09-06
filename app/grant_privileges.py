import psycopg

# Подключаемся под суперпользователем
conn = psycopg.connect(
    host="localhost",
    port="5434",
    dbname="pagila",
    user="postgres",  # суперпользователь
    password="example",  # пароль суперпользователя
)

cur = conn.cursor()

# Имя пользователя, которому будем давать права
readonly_user = "readonly_user"

cur.execute("CREATE USER readonly_user WITH PASSWORD 'readonly_password';")

# 1. Даем права на подключение к базе
cur.execute(f"GRANT CONNECT ON DATABASE pagila TO {readonly_user};")

# 2. Даем права на использование схемы public
cur.execute(f"GRANT USAGE ON SCHEMA public TO {readonly_user};")

# 3. Даем полные права на все таблицы (SELECT, INSERT, UPDATE, DELETE)
cur.execute(
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {readonly_user};"
)

# 4. Даем права на создание новых таблиц
cur.execute(f"GRANT CREATE ON SCHEMA public TO {readonly_user};")

# 5. Настраиваем права по умолчанию на будущие таблицы
cur.execute(
    f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {readonly_user};"
)


cur.execute("GRANT pg_read_all_stats TO readonly_user;")
conn.commit()

print(f"Права на изменение БД для пользователя '{readonly_user}' успешно выданы.")

cur.close()
conn.close()
