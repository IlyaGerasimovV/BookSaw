-- Инициализация базы данных PostgreSQL для Booksaw

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Настройка локали для русского языка
-- (если нужно, но обычно настраивается при создании БД)

-- Создание индексов для оптимизации поиска
-- Эти индексы будут созданы после миграций Django

-- Комментарии к базе данных
COMMENT ON DATABASE booksaw IS 'База данных для сервиса обмена книгами Booksaw';

-- Настройки для оптимизации производительности
ALTER DATABASE booksaw SET timezone TO 'Europe/Moscow';
