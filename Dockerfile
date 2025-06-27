# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        gettext \
        netcat-openbsd \
        curl \
        locales \
    && rm -rf /var/lib/apt/lists/*

# Настраиваем локаль для русского языка
RUN sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

# Копируем файл зависимостей
COPY requirements.txt /app/

# Обновляем pip и устанавливаем Python зависимости
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем entrypoint.sh ОТДЕЛЬНО и делаем исполняемым
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Копируем остальной проект
COPY . /app/

# Создаем директории для статических файлов и медиа
RUN mkdir -p /app/static /app/media /app/staticfiles

# Создаем пользователя для запуска приложения (безопасность)
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app

# Переключаемся на пользователя appuser
USER appuser

# Открываем порт
EXPOSE 8000

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Команда запуска
CMD ["/app/entrypoint.sh"]
