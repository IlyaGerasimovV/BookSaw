#!/bin/bash

# Скрипт автоматической установки Booksaw на новом компьютере

set -e

echo "🚀 Установка Booksaw - Сервис обмена книгами"
echo "=============================================="

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "Пожалуйста, установите Docker Desktop:"
    echo "Windows/Mac: https://www.docker.com/products/docker-desktop"
    echo "Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен!"
    echo "Обычно входит в состав Docker Desktop"
    exit 1
fi

echo "✅ Docker найден: $(docker --version)"
echo "✅ Docker Compose найден: $(docker-compose --version)"

# Проверка запуска Docker
if ! docker info &> /dev/null; then
    echo "❌ Docker не запущен!"
    echo "Пожалуйста, запустите Docker Desktop"
    exit 1
fi

echo "✅ Docker запущен"

# Создание директории проекта
PROJECT_DIR="booksaw-django"
if [ -d "$PROJECT_DIR" ]; then
    echo "📁 Директория $PROJECT_DIR уже существует"
    read -p "Хотите удалить её и создать заново? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_DIR"
        echo "🗑️  Старая директория удалена"
    else
        echo "ℹ️  Используем существующую директорию"
    fi
fi

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir "$PROJECT_DIR"
    echo "📁 Создана директория $PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Создание .env файла если его нет
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Настройки для разработки
DEBUG=True
SECRET_KEY=django-insecure-your-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*

# PostgreSQL настройки
DATABASE_URL=postgres://booksaw_user:booksaw_password@db:5432/booksaw
POSTGRES_DB=booksaw
POSTGRES_USER=booksaw_user
POSTGRES_PASSWORD=booksaw_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
EOF
    echo "📝 Создан файл .env"
fi

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down 2>/dev/null || true

# Сборка и запуск
echo "🔨 Сборка Docker образов..."
docker-compose build

echo "🚀 Запуск сервисов..."
docker-compose up -d

# Ожидание запуска
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка статуса
echo "📊 Статус контейнеров:"
docker-compose ps

# Проверка доступности
echo "🔍 Проверка доступности приложения..."
if curl -f http://localhost >/dev/null 2>&1; then
    echo "✅ Приложение доступно!"
else
    echo "⚠️  Приложение пока недоступно, проверьте логи:"
    echo "   docker-compose logs"
fi

echo ""
echo "🎉 Установка завершена!"
echo "================================"
echo "🌐 Основное приложение: http://localhost"
echo "⚙️  Админ-панель: http://localhost/admin"
echo "👤 Логин: admin"
echo "🔑 Пароль: admin123"
echo ""
echo "📋 Полезные команды:"
echo "   docker-compose logs     - просмотр логов"
echo "   docker-compose ps       - статус контейнеров"
echo "   docker-compose down     - остановка"
echo "   docker-compose up -d    - запуск"
echo ""
echo "📖 Подробная документация в README.md"
