from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from simple_history.models import HistoricalRecords


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название жанра")
    
    # История изменений
    history = HistoricalRecords(
        verbose_name="История жанра",
        history_change_reason_field=models.TextField(null=True, blank=True)
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"


class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    author = models.CharField(max_length=100, verbose_name="Автор")
    genres = models.ManyToManyField(Genre, verbose_name="Жанры")
    description = models.TextField(verbose_name="Описание")
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True, verbose_name="Обложка")
    book_file = models.FileField(upload_to='books/', blank=True, null=True, verbose_name="Файл книги", 
                                help_text="Загрузите файл книги (PDF, EPUB, FB2, TXT)")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    # История изменений
    history = HistoricalRecords(
        verbose_name="История книги",
        history_change_reason_field=models.TextField(null=True, blank=True),
        excluded_fields=['updated_at'],  # Исключаем поле updated_at из истории
        m2m_fields=[genres],  # Отслеживаем изменения в ManyToMany полях
    )

    def clean_title(self):
        """Валидация названия книги"""
        if not self.title:
            raise ValidationError('Название книги не может быть пустым.')

        # Убираем лишние пробелы
        self.title = self.title.strip()

        # Проверяем, что после очистки поле не стало пустым
        if not self.title:
            raise ValidationError('Название книги не может состоять только из пробелов.')

        # Проверяем максимальную длину
        if len(self.title) > 200:
            raise ValidationError('Название книги не должно превышать 200 символов.')

        # Проверяем минимальную длину
        if len(self.title) < 2:
            raise ValidationError('Название книги должно содержать минимум 2 символа.')

        return self.title

    def save(self, *args, **kwargs):
        """Переопределенный метод save с валидацией title"""
        # Валидируем поле title
        self.title = self.clean_title()

        # Вызываем родительский метод save
        super().save(*args, **kwargs)



    def __str__(self):
        return f"{self.title} - {self.author}"
    
    def get_absolute_url(self):
        return reverse('book_detail', kwargs={'pk': self.pk})
    
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum([review.rating for review in reviews]) / len(reviews), 1)
        return 0
    
    def get_change_history(self):
        """Получить историю изменений книги"""
        return self.history.all().order_by('-history_date')
    
    def get_latest_changes(self, limit=5):
        """Получить последние изменения"""
        return self.history.all().order_by('-history_date')[:limit]
    
    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        ordering = ['-created_at']


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews', verbose_name="Книга")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    text = models.TextField(verbose_name="Текст отзыва")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    # История изменений
    history = HistoricalRecords(
        verbose_name="История отзыва",
        history_change_reason_field=models.TextField(null=True, blank=True)
    )
    
    def __str__(self):
        return f"Отзыв на {self.book.title} от {self.user.username}"
    
    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = ('book', 'user')  # Один пользователь - один отзыв на книгу
        ordering = ['-created_at']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    bio = models.TextField(max_length=500, blank=True, verbose_name="О себе")
    location = models.CharField(max_length=30, blank=True, verbose_name="Местоположение")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    telegram = models.CharField(max_length=50, blank=True, verbose_name="Telegram")
    
    # История изменений
    history = HistoricalRecords(
        verbose_name="История профиля",
        history_change_reason_field=models.TextField(null=True, blank=True)
    )
    
    def __str__(self):
        return f"Профиль {self.user.username}"
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="Отправитель")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', verbose_name="Получатель")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Книга")
    subject = models.CharField(max_length=200, verbose_name="Тема")
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    
    # История изменений (в основном для отслеживания прочтения)
    history = HistoricalRecords(
        verbose_name="История сообщения",
        history_change_reason_field=models.TextField(null=True, blank=True),
        excluded_fields=['created_at']  # Исключаем created_at из истории
    )
    
    def __str__(self):
        return f"Сообщение от {self.sender.username} к {self.recipient.username}"
    
    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['-created_at']


# Кастомная модель для отслеживания действий пользователей
class UserActivity(models.Model):
    """Модель для отслеживания активности пользователей"""
    ACTION_CHOICES = [
        ('create_book', 'Создание книги'),
        ('update_book', 'Обновление книги'),
        ('delete_book', 'Удаление книги'),
        ('create_review', 'Создание отзыва'),
        ('update_review', 'Обновление отзыва'),
        ('delete_review', 'Удаление отзыва'),
        ('send_message', 'Отправка сообщения'),
        ('read_message', 'Прочтение сообщения'),
        ('update_profile', 'Обновление профиля'),
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="Действие")
    object_type = models.CharField(max_length=50, blank=True, verbose_name="Тип объекта")
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID объекта")
    description = models.TextField(blank=True, verbose_name="Описание")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP адрес")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время")
    
    # История изменений для активности (мета-уровень)
    history = HistoricalRecords(
        verbose_name="История активности",
        history_change_reason_field=models.TextField(null=True, blank=True)
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} ({self.timestamp})"
    
    class Meta:
        verbose_name = "Активность пользователя"
        verbose_name_plural = "Активность пользователей"
        ordering = ['-timestamp']
