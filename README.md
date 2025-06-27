# Booksaw - Сервис обмена книгами

Веб-приложение на Django для безвозмездного обмена книгами с использованием PostgreSQL и Docker.

## Требования

- **Docker Desktop** (Windows/Mac) или **Docker Engine** (Linux)
- **Docker Compose** (обычно входит в состав Docker Desktop)
- Минимум 4 ГБ RAM, рекомендуется 8 ГБ
- 2 ГБ свободного места на диске

## Установка Docker

### Windows/Mac
1. Скачайте и установите [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Запустите Docker Desktop
3. Убедитесь, что Docker работает: `docker --version`

### Linux (Ubuntu/Debian)
\`\`\`bash
# Обновите пакеты
sudo apt update

# Установите Docker
sudo apt install docker.io docker-compose

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Перезайдите в систему или выполните
newgrp docker
\`\`\`

## Быстрый старт

### 1. Подготовка файлов проекта
Скопируйте все файлы проекта в папку `booksaw-django` на вашем компьютере.

### 2. Создание папки static
\`\`\`bash
# Перейдите в папку проекта
cd booksaw-django

# Создайте папку static
mkdir static
\`\`\`

### 3. Запуск приложения
\`\`\`bash
# Сборка и запуск всех сервисов
docker-compose up --build -d
\`\`\`

### 4. Проверка статуса
\`\`\`bash
# Проверка статуса контейнеров
docker-compose ps
\`\`\`

### 5. Доступ к приложению
- **Основное приложение**: http://localhost
- **Админ-панель**: http://localhost/admin
  - Логин: `admin`
  - Пароль: `admin123`

## Основные команды Docker Compose

### Управление сервисами
\`\`\`bash
# Запуск всех сервисов
docker-compose up -d

# Запуск с пересборкой образов
docker-compose up --build -d

# Остановка всех сервисов
docker-compose down

# Перезапуск всех сервисов
docker-compose restart

# Перезапуск конкретного сервиса
docker-compose restart web
docker-compose restart db
docker-compose restart nginx
\`\`\`

### Просмотр логов
\`\`\`bash
# Логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker-compose logs web
docker-compose logs db
docker-compose logs nginx

# Логи в реальном времени
docker-compose logs -f
docker-compose logs -f web

# Последние 50 строк логов
docker-compose logs --tail=50 web
\`\`\`

### Проверка статуса
\`\`\`bash
# Статус всех контейнеров
docker-compose ps

# Подробная информация о контейнерах
docker-compose top
\`\`\`

## Работа с базой данных

### Подключение к PostgreSQL
\`\`\`bash
# Подключение к базе данных
docker-compose exec db psql -U booksaw_user -d booksaw

# В PostgreSQL выполните:
\l                    # список баз данных
\dt                   # список таблиц
\d books_book         # структура таблицы книг
\q                    # выход
\`\`\`

### Миграции Django
\`\`\`bash
# Проверка статуса миграций
docker-compose exec web python manage.py showmigrations

# Создание новых миграций
docker-compose exec web python manage.py makemigrations

# Применение миграций
docker-compose exec web python manage.py migrate

# Применение конкретной миграции
docker-compose exec web python manage.py migrate books 0001

# Откат миграции
docker-compose exec web python manage.py migrate books 0001
\`\`\`

### Работа с данными
\`\`\`bash
# Django shell
docker-compose exec web python manage.py shell

# Создание суперпользователя
docker-compose exec web python manage.py createsuperuser

# Сбор статических файлов
docker-compose exec web python manage.py collectstatic

# Очистка сессий
docker-compose exec web python manage.py clearsessions
\`\`\`

## Резервное копирование и восстановление

### Создание бэкапа
\`\`\`bash
# Создание бэкапа базы данных
docker-compose exec db pg_dump -U booksaw_user booksaw > backup_$(date +%Y%m%d_%H%M%S).sql

# Создание бэкапа с сжатием
docker-compose exec db pg_dump -U booksaw_user -Fc booksaw > backup_$(date +%Y%m%d_%H%M%S).dump
\`\`\`

### Восстановление из бэкапа
\`\`\`bash
# Восстановление из SQL файла
docker-compose exec -T db psql -U booksaw_user -d booksaw < backup_file.sql

# Восстановление из dump файла
docker-compose exec db pg_restore -U booksaw_user -d booksaw backup_file.dump
\`\`\`

### Бэкап медиа файлов
\`\`\`bash
# Создание архива медиа файлов
docker-compose exec web tar -czf /tmp/media_backup.tar.gz -C /app media

# Копирование архива на хост
docker cp $(docker-compose ps -q web):/tmp/media_backup.tar.gz ./media_backup.tar.gz
\`\`\`

## Отладка и устранение неполадок

### Просмотр логов ошибок
\`\`\`bash
# Поиск ошибок в логах
docker-compose logs web | grep -i error
docker-compose logs db | grep -i error

# Последние ошибки
docker-compose logs --tail=100 web | grep -i "error\|exception\|traceback"
\`\`\`

### Подключение к контейнерам
\`\`\`bash
# Подключение к контейнеру web
docker-compose exec web bash

# Подключение к контейнеру базы данных
docker-compose exec db bash

# Выполнение команды в контейнере
docker-compose exec web ls -la /app
\`\`\`

### Проверка ресурсов
\`\`\`bash
# Использование ресурсов контейнерами
docker stats

# Информация о Docker
docker system df

# Очистка неиспользуемых ресурсов
docker system prune
\`\`\`

## Полная очистка и переустановка

### Остановка и удаление всех данных
\`\`\`bash
# Остановка и удаление контейнеров с данными
docker-compose down -v

# Удаление образов (опционально)
docker-compose down --rmi all

# Очистка системы Docker
docker system prune -a
\`\`\`

### Переустановка с нуля
\`\`\`bash
# Полная очистка
docker-compose down -v
docker system prune -f

# Создание папки static
mkdir -p static

# Запуск заново
docker-compose up --build -d
\`\`\`

## Мониторинг

### Проверка работоспособности
\`\`\`bash
# Проверка доступности приложения
curl -f http://localhost || echo "Приложение недоступно"

# Проверка админ-панели
curl -f http://localhost/admin/ || echo "Админ-панель недоступна"

# Проверка базы данных
docker-compose exec db pg_isready -U booksaw_user
\`\`\`

### Мониторинг ресурсов
\`\`\`bash
# Использование CPU и памяти
docker-compose exec web top

# Использование диска
docker-compose exec web df -h

# Процессы в контейнере
docker-compose exec web ps aux
\`\`\`

## Разработка

### Режим разработки
\`\`\`bash
# Запуск в режиме разработки (если есть docker-compose.dev.yml)
docker-compose -f docker-compose.dev.yml up -d

# Просмотр изменений в реальном времени
docker-compose logs -f web
\`\`\`

### Установка новых зависимостей
\`\`\`bash
# Установка пакета Python
docker-compose exec web pip install package_name

# Обновление requirements.txt
docker-compose exec web pip freeze > requirements.txt

# Пересборка образа с новыми зависимостями
docker-compose build web
\`\`\`

## Часто используемые команды

\`\`\`bash
# Быстрый перезапуск
docker-compose restart web

# Просмотр логов последних 5 минут
docker-compose logs --since 5m web

# Выполнение команды Django
docker-compose exec web python manage.py <команда>

# Копирование файла из контейнера
docker cp $(docker-compose ps -q web):/app/file.txt ./

# Копирование файла в контейнер
docker cp ./file.txt $(docker-compose ps -q web):/app/
\`\`\`

## Порты и сервисы

- **80** - Nginx (основной доступ)
- **8000** - Django (прямой доступ)
- **5432** - PostgreSQL (доступ к базе данных)

## Переменные окружения

Основные переменные в файле `.env`:
- `DEBUG` - режим отладки (True/False)
- `SECRET_KEY` - секретный ключ Django
- `DATABASE_URL` - URL подключения к базе данных
- `ALLOWED_HOSTS` - разрешенные хосты

## Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs`
2. Убедитесь, что все контейнеры запущены: `docker-compose ps`
3. Проверьте доступность портов: `netstat -tulpn | grep :80`
4. Перезапустите сервисы: `docker-compose restart`
5. В крайнем случае: полная переустановка

## Структура проекта

\`\`\`
booksaw-django/
├── docker-compose.yml      # Конфигурация Docker Compose
├── Dockerfile             # Образ Django приложения
├── nginx.conf             # Конфигурация Nginx
├── entrypoint.sh          # Скрипт инициализации
├── requirements.txt       # Python зависимости
├── .env                   # Переменные окружения
├── manage.py              # Django управление
├── booksaw/               # Основные настройки Django
├── books/                 # Приложение книг
├── templates/             # HTML шаблоны
├── static/                # Статические файлы (создать вручную)
└── media/                 # Загруженные файлы
