#!/bin/bash

# Делаем скрипт исполняемым
set -e

# Функция для ожидания PostgreSQL
wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    until nc -z $POSTGRES_HOST $POSTGRES_PORT; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "PostgreSQL is up - continuing..."
}

# Функция для проверки подключения к базе данных
check_db_connection() {
    echo "Checking database connection..."
    python -c "
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booksaw.settings')
django.setup()

from django.db import connections
from django.core.exceptions import ImproperlyConfigured

try:
    db_conn = connections['default']
    with db_conn.cursor() as cursor:
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        if result:
            print('Database connection successful!')
        else:
            print('Database connection failed: No result')
            sys.exit(1)
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
"
}

# Устанавливаем переменные окружения по умолчанию
export POSTGRES_HOST=${POSTGRES_HOST:-db}
export POSTGRES_PORT=${POSTGRES_PORT:-5432}

# Ждем PostgreSQL
wait_for_postgres

# Проверяем подключение к базе данных
check_db_connection

# Выполняем миграции
echo "Running migrations..."
python manage.py migrate --noinput

# Создаем суперпользователя если его нет
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth.models import User
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@booksaw.local', 'admin123')
        print('Superuser created: admin/admin123')
    else:
        print('Superuser already exists')
except Exception as e:
    print(f'Error creating superuser: {e}')
"

# Создаем жанры
echo "Creating genres..."
python manage.py shell -c "
from books.models import Genre
try:
    genres = [
        'Классическая литература', 'Современная проза', 'Фантастика',
        'Фэнтези', 'Детектив', 'Роман', 'Поэзия', 'Биография',
        'История', 'Философия', 'Психология', 'Научная литература',
        'Детская литература', 'Приключения', 'Мистика', 'Антиутопия',
        'Триллер', 'Ужасы', 'Комедия', 'Драма', 'Научпоп'
    ]
    created_count = 0
    for genre_name in genres:
        genre, created = Genre.objects.get_or_create(name=genre_name)
        if created:
            created_count += 1
    print(f'Created {created_count} new genres, total: {Genre.objects.count()}')
except Exception as e:
    print(f'Error creating genres: {e}')
"

# Создаем тестовые данные (опционально)
echo "Creating test data..."
python manage.py shell -c "
from django.contrib.auth.models import User
from books.models import Book, Genre, UserProfile
import random

try:
    # Создаем тестовых пользователей
    test_users = [
        ('testuser1', 'test1@example.com', 'Иван', 'Петров'),
        ('testuser2', 'test2@example.com', 'Мария', 'Сидорова'),
        ('testuser3', 'test3@example.com', 'Алексей', 'Иванов'),
    ]

    for username, email, first_name, last_name in test_users:
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                password='testpass123',
                first_name=first_name,
                last_name=last_name
            )
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'bio': f'Любитель чтения, пользователь {username}',
                    'location': 'Москва'
                }
            )
            print(f'Created test user: {username}')

    # Создаем тестовые книги
    if Book.objects.count() < 5:
        test_books = [
            ('Война и мир', 'Лев Толстой', 'Классическая литература', 'Великий роман о войне 1812 года'),
            ('1984', 'Джордж Оруэлл', 'Антиутопия', 'Роман-предупреждение о тоталитарном обществе'),
            ('Мастер и Маргарита', 'Михаил Булгаков', 'Современная проза', 'Мистический роман о добре и зле'),
            ('Гарри Поттер и философский камень', 'Дж.К. Роулинг', 'Фэнтези', 'Первая книга о юном волшебнике'),
            ('Преступление и наказание', 'Федор Достоевский', 'Классическая литература', 'Психологический роман о преступлении'),
        ]
        
        users = list(User.objects.filter(username__startswith='testuser'))
        genres = Genre.objects.all()
        
        for title, author, genre_name, description in test_books:
            if not Book.objects.filter(title=title).exists():
                genre = genres.filter(name=genre_name).first()
                if genre and users:
                    book = Book.objects.create(
                        title=title,
                        author=author,
                        description=description,
                        owner=random.choice(users)
                    )
                    book.genres.add(genre)
                    print(f'Created test book: {title}')

    print('Test data creation completed!')
except Exception as e:
    print(f'Error creating test data: {e}')
"

# Собираем статические файлы
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Setup completed successfully!"
echo "Access the application at: http://localhost"
echo "Admin panel: http://localhost/admin (admin/admin123)"
echo "Test users: testuser1, testuser2, testuser3 (password: testpass123)"

# Запускаем Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn booksaw.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120 --access-logfile - --error-logfile -
