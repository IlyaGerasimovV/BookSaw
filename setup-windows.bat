@echo off
echo 🚀 Установка Booksaw - Сервис обмена книгами
echo ==============================================

REM Проверка наличия Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker не установлен!
    echo Пожалуйста, установите Docker Desktop:
    echo https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Проверка наличия Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose не установлен!
    echo Обычно входит в состав Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker найден
echo ✅ Docker Compose найден

REM Проверка запуска Docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker не запущен!
    echo Пожалуйста, запустите Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker запущен

REM Создание .env файла если его нет
if not exist ".env" (
    echo # Настройки для разработки > .env
    echo DEBUG=True >> .env
    echo SECRET_KEY=django-insecure-your-secret-key-change-this-in-production >> .env
    echo ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,* >> .env
    echo. >> .env
    echo # PostgreSQL настройки >> .env
    echo DATABASE_URL=postgres://booksaw_user:booksaw_password@db:5432/booksaw >> .env
    echo POSTGRES_DB=booksaw >> .env
    echo POSTGRES_USER=booksaw_user >> .env
    echo POSTGRES_PASSWORD=booksaw_password >> .env
    echo POSTGRES_HOST=db >> .env
    echo POSTGRES_PORT=5432 >> .env
    echo 📝 Создан файл .env
)

REM Остановка существующих контейнеров
echo 🛑 Остановка существующих контейнеров...
docker-compose down 2>nul

REM Сборка и запуск
echo 🔨 Сборка Docker образов...
docker-compose build

echo 🚀 Запуск сервисов...
docker-compose up -d

REM Ожидание запуска
echo ⏳ Ожидание запуска сервисов...
timeout /t 10 /nobreak >nul

REM Проверка статуса
echo 📊 Статус контейнеров:
docker-compose ps

echo.
echo 🎉 Установка завершена!
echo ================================
echo 🌐 Основное приложение: http://localhost
echo ⚙️  Админ-панель: http://localhost/admin
echo 👤 Логин: admin
echo 🔑 Пароль: admin123
echo.
echo 📋 Полезные команды:
echo    docker-compose logs     - просмотр логов
echo    docker-compose ps       - статус контейнеров
echo    docker-compose down     - остановка
echo    docker-compose up -d    - запуск
echo.
echo 📖 Подробная документация в README.md

pause
