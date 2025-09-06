import psycopg2
import random
import string


# Функция для генерации случайного имени
def generate_random_name(length=10):
    return "".join(random.choices(string.ascii_letters, k=length))


# Функция для генерации случайного email
def generate_random_email():
    domains = ["example.com", "test.com", "demo.com"]
    name = generate_random_name(10)
    domain = random.choice(domains)
    return f"{name}@{domain}"


# Подключение к базе данных
conn = psycopg2.connect(
    host="localhost",
    port="5433",
    database="mydb",
    user="postgres",
    password="example",
)

cur = conn.cursor()
res = cur.execute("Select * from users;")

# Генерация 100 случайных пользователей и их вставка в таблицу
for _ in range(100):
    name = generate_random_name()
    email = generate_random_email()

    # Вставка записи в таблицу
    cur.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))

# Подтверждение изменений
conn.commit()

# Закрытие соединения
cur.close()
conn.close()

print("100 записей успешно добавлены!")
