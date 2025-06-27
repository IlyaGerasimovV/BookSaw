# Makefile для управления Docker-контейнерами Booksaw

.PHONY: help build up down logs shell migrate createsuperuser test clean lint format

# Показать справку
help:
	@echo "Доступные команды:"
	@echo "  build          - Собрать Docker образы"
	@echo "  up             - Запустить все сервисы"
	@echo "  down           - Остановить все сервисы"
	@echo "  logs           - Показать логи"
	@echo "  shell          - Открыть shell в контейнере web"
	@echo "  dbshell        - Открыть PostgreSQL shell"
	@echo "  migrate        - Выполнить миграции"
	@echo "  createsuperuser - Создать суперпользователя"
	@echo "  test           - Запустить тесты"
	@echo "  clean          - Очистить все данные"
	@echo "  backup         - Создать бэкап базы данных"
	@echo "  restore        - Восстановить базу данных из бэкапа"
	@echo ""
	@echo "Команды для разработки:"
	@echo "  install-dev    - Установить dev зависимости"
	@echo "  lint           - Проверить код линтерами"
	@echo "  format         - Форматировать код"
	@echo "  check          - Форматирование + линтинг"
	@echo "  security       - Проверка безопасности"
	@echo "  quality        - Полный анализ качества кода"

# Собрать образы
build:
	docker-compose build

# Запустить все сервисы
up:
	docker-compose up -d

# Остановить все сервисы
down:
	docker-compose down

# Показать логи
logs:
	docker-compose logs -f

# Открыть shell в контейнере web
shell:
	docker-compose exec web python manage.py shell

# Открыть PostgreSQL shell
dbshell:
	docker-compose exec db psql -U booksaw_user -d booksaw

# Выполнить миграции
migrate:
	docker-compose exec web python manage.py migrate

# Создать суперпользователя
createsuperuser:
	docker-compose exec web python manage.py createsuperuser

# Запустить тесты
test:
	docker-compose exec web python manage.py test

# Очистить все данные
clean:
	docker-compose down -v
	docker system prune -f

# Создать бэкап базы данных
backup:
	docker-compose exec db pg_dump -U booksaw_user booksaw > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Восстановить базу данных из бэкапа
restore:
	@read -p "Введите имя файла бэкапа: " backup_file; \
	docker-compose exec -T db psql -U booksaw_user -d booksaw < $$backup_file

# Перезапустить сервисы
restart: down up

# Показать статус сервисов
status:
	docker-compose ps

# Обновить зависимости
update:
	docker-compose exec web pip install -r requirements.txt --upgrade

# === КОМАНДЫ ДЛЯ РАЗРАБОТКИ ===

# Установка dev зависимостей
install-dev:
	@echo "📦 Установка dev зависимостей..."
	docker-compose exec web pip install -r requirements-dev.txt

# Форматирование кода
format:
	@echo "🎨 Форматирование кода с помощью Black..."
	docker-compose exec web black .
	@echo "📦 Сортировка импортов с помощью isort..."
	docker-compose exec web isort .

# Проверка кода
lint:
	@echo "🔍 Проверка кода с помощью flake8..."
	docker-compose exec web flake8 .
	@echo "🔍 Проверка кода с помощью pylint..."
	docker-compose exec web pylint books/ booksaw/ --load-plugins=pylint_django --django-settings-module=booksaw.settings || true
	@echo "🔍 Проверка типов с помощью mypy..."
	docker-compose exec web mypy . || true

# Полная проверка (форматирование + линтинг)
check: format lint
	@echo "✅ Проверка завершена!"

# Установка pre-commit хуков
setup-hooks:
	docker-compose exec web pre-commit install

# Запуск pre-commit на всех файлах
pre-commit-all:
	docker-compose exec web pre-commit run --all-files

# Быстрая проверка только измененных файлов
quick-check:
	@echo "⚡ Быстрая проверка..."
	docker-compose exec web black --check . || true
	docker-compose exec web isort --check-only . || true
	docker-compose exec web flake8 . --select=E9,F63,F7,F82 || true

# Проверка безопасности
security:
	@echo "🔒 Проверка безопасности..."
	docker-compose exec web pip install bandit safety
	docker-compose exec web bandit -r . -x tests,migrations || true
	docker-compose exec web safety check || true

# Анализ сложности кода
complexity:
	@echo "📊 Анализ сложности кода..."
	docker-compose exec web pip install radon
	docker-compose exec web radon cc . --min B || true
	docker-compose exec web radon mi . --min B || true

# Проверка покрытия тестов
coverage:
	@echo "📈 Проверка покрытия тестов..."
	docker-compose exec web pip install coverage
	docker-compose exec web coverage run --source='.' manage.py test
	docker-compose exec web coverage report
	docker-compose exec web coverage html

# Полный анализ качества кода
quality: check security complexity coverage
	@echo "🏆 Полный анализ качества завершен!"

# Запуск в режиме разработки
dev:
	@echo "🚀 Запуск в режиме разработки..."
	docker-compose -f docker-compose.dev.yml up -d

# Остановка режима разработки
dev-down:
	docker-compose -f docker-compose.dev.yml down

# Логи в режиме разработки
dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Создание миграций
makemigrations:
	docker-compose exec web python manage.py makemigrations

# Сбор статических файлов
collectstatic:
	docker-compose exec web python manage.py collectstatic --noinput

# Создание фикстур
dumpdata:
	docker-compose exec web python manage.py dumpdata books --indent 2 > fixtures/books_data.json

# Загрузка фикстур
loaddata:
	docker-compose exec web python manage.py loaddata fixtures/books_data.json
