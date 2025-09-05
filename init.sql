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

-- Предоставление прав на подключение ко всем базам данных
GRANT CONNECT ON DATABASE postgres TO readonly_user;

-- Предоставление прав на использование схемы во всех базах данных (если требуется)
GRANT USAGE ON SCHEMA public TO readonly_user;

-- Для того, чтобы задать привилегии на все таблицы в базах данных:
DO $$ 
DECLARE
    db RECORD;
BEGIN
    -- Перебор всех баз данных
    FOR db IN
        SELECT datname FROM pg_database WHERE datistemplate = false AND datname <> 'postgres'
    LOOP
        -- Подключение к каждой базе данных и назначение прав на таблицы
        EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user', db.datname);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user', db.datname);
    END LOOP;
END $$;


