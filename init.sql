-- Создание таблицы, если её нет
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE
);

-- Вставка данных в таблицу
INSERT INTO users (name, email) VALUES
('John Doe', 'john@example.com'),
('Jane Smith', 'jane@example.com');

-- Создание пользователя с правами только на чтение
CREATE USER readonly_user WITH PASSWORD 'readonly_password';

-- Предоставление прав на подключение, использование схемы и чтение всех таблиц
GRANT CONNECT ON DATABASE mydb TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Настройка дефолтных привилегий для новых таблиц
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;

