# Makefile для линтинга и форматирования кода

.PHONY: lint format check install-dev

# Установка dev зависимостей
install-dev:
	docker-compose exec web pip install black isort flake8 pylint mypy pre-commit django-stubs djangorestframework-stubs

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
	docker-compose exec web pylint books/ booksaw/ --load-plugins=pylint_django --django-settings-module=booksaw.settings
	@echo "🔍 Проверка типов с помощью mypy..."
	docker-compose exec web mypy .

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
	docker-compose exec web black --check .
	docker-compose exec web isort --check-only .
	docker-compose exec web flake8 . --select=E9,F63,F7,F82

# Проверка безопасности
security:
	@echo "🔒 Проверка безопасности..."
	docker-compose exec web pip install bandit safety
	docker-compose exec web bandit -r . -x tests,migrations
	docker-compose exec web safety check

# Анализ сложности кода
complexity:
	@echo "📊 Анализ сложности кода..."
	docker-compose exec web pip install radon
	docker-compose exec web radon cc . --min B
	docker-compose exec web radon mi . --min B

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

# Помощь
help:
	@echo "Доступные команды для линтинга:"
	@echo "  install-dev     - Установить dev зависимости"
	@echo "  format          - Форматировать код (black + isort)"
	@echo "  lint            - Проверить код (flake8 + pylint + mypy)"
	@echo "  check           - Форматирование + линтинг"
	@echo "  quick-check     - Быстрая проверка"
	@echo "  setup-hooks     - Установить pre-commit хуки"
	@echo "  pre-commit-all  - Запустить pre-commit на всех файлах"
	@echo "  security        - Проверка безопасности"
	@echo "  complexity      - Анализ сложности кода"
	@echo "  coverage        - Проверка покрытия тестов"
	@echo "  quality         - Полный анализ качества"
