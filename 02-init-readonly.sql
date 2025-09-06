-- Активируем расширение
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Создаём пользователя только для чтения
CREATE USER readonly_user WITH PASSWORD 'readonly_password';

-- Даём права на подключение и чтение
GRANT CONNECT ON DATABASE pagila TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Выдаём права на автоматическое чтение всех будущих таблиц
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
