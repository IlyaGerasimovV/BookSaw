"""Ресурсы для экспорта/импорта данных"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, DateTimeWidget
from django.contrib.auth.models import User
from .models import Book, Review, Genre, UserProfile, Message


class GenreResource(resources.ModelResource):
    """Ресурс для экспорта/импорта жанров"""
    
    class Meta:
        model = Genre
        fields = ('id', 'name')
        export_order = ('id', 'name')
    
    def get_export_queryset(self, queryset):
        """Кастомизация queryset для экспорта"""
        # Экспортируем только жанры, у которых есть книги
        return queryset.filter(book__isnull=False).distinct()
    
    def dehydrate_name(self, genre):
        """Кастомизация поля name при экспорте"""
        return f"Жанр: {genre.name}"
    
    def get_name(self, instance):
        """Альтернативный метод получения имени"""
        return instance.name.upper()


class BookResource(resources.ModelResource):
    """Ресурс для экспорта/импорта книг"""
    # Кастомные поля
    owner = fields.Field(
        column_name='owner',
        attribute='owner',
        widget=ForeignKeyWidget(User, 'username')
    )
    genres = fields.Field(
        column_name='genres',
        attribute='genres',
        widget=ManyToManyWidget(Genre, field='name', separator='|')
    )
    average_rating = fields.Field(
        column_name='average_rating',
        readonly=True
    )
    reviews_count = fields.Field(
        column_name='reviews_count',
        readonly=True
    )
    has_file = fields.Field(
        column_name='has_file',
        readonly=True
    )
    created_at_formatted = fields.Field(
        column_name='created_at_formatted',
        attribute='created_at',
        widget=DateTimeWidget(format='%d.%m.%Y %H:%M'),
        readonly=True
    )
    class Meta:
        model = Book
        fields = (
            'id', 'title', 'author', 'description', 'owner', 'genres',
            'average_rating', 'reviews_count', 'has_file', 
            'created_at', 'created_at_formatted', 'updated_at'
        )
        export_order = (
            'id', 'title', 'author', 'owner', 'genres', 'description',
            'average_rating', 'reviews_count', 'has_file', 'created_at_formatted'
        )
    
    def get_export_queryset(self, queryset):
        """Кастомизация queryset для экспорта"""
        # Экспортируем только книги с обложками и файлами
        return queryset.exclude(cover_image='').exclude(book_file='').select_related('owner').prefetch_related('genres', 'reviews')
    
    def dehydrate_title(self, book):
        """Кастомизация поля title при экспорте"""
        return f"{book.title} ({book.author})"
    
    def dehydrate_description(self, book):
        """Кастомизация описания - обрезаем до 100 символов"""
        if len(book.description) > 100:
            return book.description[:100] + "..."
        return book.description
    
    def dehydrate_average_rating(self, book):
        """Добавляем средний рейтинг"""
        return book.average_rating()
    
    def dehydrate_reviews_count(self, book):
        """Добавляем количество отзывов"""
        return book.reviews.count()
    
    def dehydrate_has_file(self, book):
        """Проверяем наличие файла"""
        return "Да" if book.book_file else "Нет"
    
    def get_title(self, instance):
        """Альтернативный метод получения названия"""
        return instance.title.title()
    
    def get_author(self, instance):
        """Альтернативный метод получения автора"""
        return instance.author.title()
    
    def get_owner_info(self, instance):
        """Получение информации о владельце"""
        return f"{instance.owner.get_full_name()} ({instance.owner.username})"


class ReviewResource(resources.ModelResource):
    """Ресурс для экспорта/импорта отзывов"""
    
    book = fields.Field(
        column_name='book',
        attribute='book',
        widget=ForeignKeyWidget(Book, 'title')
    )
    
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )
    
    rating_stars = fields.Field(
        column_name='rating_stars',
        readonly=True
    )
    
    text_preview = fields.Field(
        column_name='text_preview',
        readonly=True
    )
    
    class Meta:
        model = Review
        fields = (
            'id', 'book', 'user', 'text', 'text_preview', 
            'rating', 'rating_stars', 'created_at'
        )
        export_order = (
            'id', 'book', 'user', 'rating', 'rating_stars', 
            'text_preview', 'created_at'
        )
    
    def get_export_queryset(self, queryset):
        """Кастомизация queryset для экспорта"""
        # Экспортируем только отзывы с рейтингом 4 и выше
        return queryset.filter(rating__gte=4).select_related('book', 'user').order_by('-rating', '-created_at')
    
    def dehydrate_rating_stars(self, review):
        """Преобразуем рейтинг в звездочки"""
        return "★" * review.rating + "☆" * (5 - review.rating)
    
    def dehydrate_text_preview(self, review):
        """Создаем превью текста отзыва"""
        if len(review.text) > 50:
            return review.text[:50] + "..."
        return review.text
    
    def get_rating(self, instance):
        """Альтернативный метод получения рейтинга"""
        return f"{instance.rating}/5"


class UserProfileResource(resources.ModelResource):
    """Ресурс для экспорта/импорта профилей пользователей"""
    
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )
    
    full_name = fields.Field(
        column_name='full_name',
        readonly=True
    )
    
    books_count = fields.Field(
        column_name='books_count',
        readonly=True
    )
    
    reviews_count = fields.Field(
        column_name='reviews_count',
        readonly=True
    )
    
    has_avatar = fields.Field(
        column_name='has_avatar',
        readonly=True
    )
    
    class Meta:
        model = UserProfile
        fields = (
            'id', 'user', 'full_name', 'bio', 'location', 
            'phone', 'telegram', 'books_count', 'reviews_count', 'has_avatar'
        )
        export_order = (
            'id', 'user', 'full_name', 'location', 'phone', 'telegram',
            'books_count', 'reviews_count', 'bio', 'has_avatar'
        )
    
    def get_export_queryset(self, queryset):
        """Кастомизация queryset для экспорта"""
        # Экспортируем только активных пользователей с заполненными профилями
        return queryset.exclude(bio='').exclude(location='').select_related('user')
    
    def dehydrate_full_name(self, profile):
        """Получаем полное имя пользователя"""
        return profile.user.get_full_name() or profile.user.username
    
    def dehydrate_books_count(self, profile):
        """Количество книг пользователя"""
        return profile.user.book_set.count()
    
    def dehydrate_reviews_count(self, profile):
        """Количество отзывов пользователя"""
        return profile.user.review_set.count()
    
    def dehydrate_has_avatar(self, profile):
        """Проверяем наличие аватара"""
        return "Да" if profile.avatar else "Нет"
    
    def get_bio(self, instance):
        """Альтернативный метод получения биографии"""
        return instance.bio[:100] + "..." if len(instance.bio) > 100 else instance.bio


class MessageResource(resources.ModelResource):
    """Ресурс для экспорта/импорта сообщений"""
    
    sender = fields.Field(
        column_name='sender',
        attribute='sender',
        widget=ForeignKeyWidget(User, 'username')
    )
    
    recipient = fields.Field(
        column_name='recipient',
        attribute='recipient',
        widget=ForeignKeyWidget(User, 'username')
    )
    
    book = fields.Field(
        column_name='book',
        attribute='book',
        widget=ForeignKeyWidget(Book, 'title')
    )
    
    message_preview = fields.Field(
        column_name='message_preview',
        readonly=True
    )
    
    status = fields.Field(
        column_name='status',
        readonly=True
    )
    
    class Meta:
        model = Message
        fields = (
            'id', 'sender', 'recipient', 'book', 'subject', 
            'message_preview', 'status', 'created_at'
        )
        export_order = (
            'id', 'sender', 'recipient', 'book', 'subject', 
            'message_preview', 'status', 'created_at'
        )
    
    def get_export_queryset(self, queryset):
        """Кастомизация queryset для экспорта"""
        # Экспортируем только прочитанные сообщения за последний месяц
        from django.utils import timezone
        from datetime import timedelta
        last_month = timezone.now() - timedelta(days=30)
        return queryset.filter(is_read=True, created_at__gte=last_month).select_related('sender', 'recipient', 'book')
    
    def dehydrate_message_preview(self, message):
        """Создаем превью сообщения"""
        if len(message.message) > 100:
            return message.message[:100] + "..."
        return message.message
    
    def dehydrate_status(self, message):
        """Статус сообщения"""
        return "Прочитано" if message.is_read else "Не прочитано"
    
    def get_subject(self, instance):
        """Альтернативный метод получения темы"""
        return instance.subject.title()
