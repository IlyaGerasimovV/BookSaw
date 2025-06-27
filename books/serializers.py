from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, Review, Genre, UserProfile, Message, UserActivity


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""
    full_name = serializers.SerializerMethodField()
    books_count = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'full_name', 'date_joined', 'books_count', 'reviews_count']
        read_only_fields = ['id', 'date_joined', 'books_count', 'reviews_count']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    
    def get_books_count(self, obj):
        return obj.book_set.count()
    
    def get_reviews_count(self, obj):
        return obj.review_set.count()


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'bio', 'location', 'birth_date', 
                 'avatar', 'phone', 'telegram']
        read_only_fields = ['id']


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для жанра"""
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Genre
        fields = ['id', 'name', 'books_count']
        read_only_fields = ['id', 'books_count']
    
    def get_books_count(self, obj):
        return obj.book_set.count()


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отзыва"""
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    book_title = serializers.CharField(source='book.title', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'book', 'book_title', 'user', 'user_id', 
                 'text', 'rating', 'created_at']
        read_only_fields = ['id', 'created_at', 'user']
    
    def create(self, validated_data):
        # Автоматически устанавливаем текущего пользователя
        validated_data['user'] = self.context['request'].user
        review = super().create(validated_data)
        review._change_reason = "Создан через API"
        review.save()
        return review
    
    def update(self, instance, validated_data):
        instance._change_reason = "Обновлен через API"
        return super().update(instance, validated_data)


class BookListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка книг (упрощенный)"""
    owner = UserSerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    has_file = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'description', 'cover_image', 
                 'owner', 'genres', 'average_rating', 'reviews_count', 
                 'has_file', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        return obj.average_rating()
    
    def get_reviews_count(self, obj):
        return obj.reviews.count()
    
    def get_has_file(self, obj):
        return bool(obj.book_file)


class BookDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о книге"""
    owner = UserSerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    genre_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(), 
        many=True, 
        write_only=True,
        source='genres'
    )
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    has_file = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'description', 'cover_image', 
                 'book_file', 'owner', 'genres', 'genre_ids', 'reviews',
                 'average_rating', 'reviews_count', 'has_file', 'file_size',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']
    
    def get_average_rating(self, obj):
        return obj.average_rating()
    
    def get_reviews_count(self, obj):
        return obj.reviews.count()
    
    def get_has_file(self, obj):
        return bool(obj.book_file)
    
    def get_file_size(self, obj):
        if obj.book_file:
            try:
                return obj.book_file.size
            except:
                return None
        return None
    
    def create(self, validated_data):
        # Автоматически устанавливаем текущего пользователя как владельца
        validated_data['owner'] = self.context['request'].user
        book = super().create(validated_data)
        book._change_reason = "Создана через API"
        book.save()
        return book
    
    def update(self, instance, validated_data):
        instance._change_reason = "Обновлена через API"
        return super().update(instance, validated_data)


class BookCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления книги"""
    genre_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(), 
        many=True,
        source='genres'
    )
    
    class Meta:
        model = Book
        fields = ['title', 'author', 'description', 'cover_image', 
                 'book_file', 'genre_ids']
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        book = super().create(validated_data)
        book._change_reason = "Создана через API"
        book.save()
        return book
    
    def update(self, instance, validated_data):
        instance._change_reason = "Обновлена через API"
        return super().update(instance, validated_data)


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор для сообщений"""
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    book_id = serializers.IntegerField(write_only=True)
    recipient_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'recipient_id', 'book', 
                 'book_id', 'subject', 'message', 'created_at', 'is_read']
        read_only_fields = ['id', 'created_at', 'sender']
    
    def create(self, validated_data):
        # Автоматически устанавливаем отправителя
        validated_data['sender'] = self.context['request'].user
        
        # Если получатель не указан, берем владельца книги
        if 'recipient_id' not in validated_data:
            book = Book.objects.get(id=validated_data['book_id'])
            validated_data['recipient'] = book.owner
        else:
            validated_data['recipient'] = User.objects.get(id=validated_data['recipient_id'])
        
        # Удаляем временные поля
        validated_data.pop('recipient_id', None)
        book_id = validated_data.pop('book_id')
        validated_data['book'] = Book.objects.get(id=book_id)
        
        message = super().create(validated_data)
        message._change_reason = "Создано через API"
        message.save()
        return message


class BookStatisticsSerializer(serializers.Serializer):
    """Сериализатор для статистики книг"""
    total_books = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_reviews = serializers.IntegerField()
    average_rating = serializers.FloatField()
    books_with_files = serializers.IntegerField()
    most_popular_genre = serializers.CharField()


# Новые сериализаторы для истории
class HistoryRecordSerializer(serializers.Serializer):
    """Сериализатор для записи истории"""
    history_id = serializers.CharField()
    history_date = serializers.DateTimeField()
    history_change_reason = serializers.CharField()
    history_type = serializers.CharField()
    history_user = serializers.SerializerMethodField()
    
    def get_history_user(self, obj):
        if hasattr(obj, 'history_user') and obj.history_user:
            return obj.history_user.username
        return None


class UserActivitySerializer(serializers.ModelSerializer):
    """Сериализатор для активности пользователя"""
    user = UserSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'action', 'action_display', 'object_type', 
                 'object_id', 'description', 'ip_address', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class BookHistorySerializer(serializers.Serializer):
    """Сериализатор для истории книги"""
    book = BookListSerializer()
    history = HistoryRecordSerializer(many=True)
    total_changes = serializers.IntegerField()


class UserTimelineSerializer(serializers.Serializer):
    """Сериализатор для временной линии пользователя"""
    date = serializers.DateTimeField()
    type = serializers.CharField()
    action = serializers.CharField()
    description = serializers.CharField()
    object_id = serializers.IntegerField()
