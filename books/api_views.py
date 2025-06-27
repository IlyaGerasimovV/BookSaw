from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Max, Min
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
import json

from .models import Book, Review, Genre, UserProfile, Message, UserActivity
from .serializers import (
    BookListSerializer, BookDetailSerializer, BookCreateUpdateSerializer,
    ReviewSerializer, GenreSerializer, UserSerializer, UserProfileSerializer,
    MessageSerializer, BookStatisticsSerializer, UserActivitySerializer
)
from .pagination import (
    BookPagination, ReviewPagination, MessagePagination, 
    CustomPageNumberPagination, SmallResultsSetPagination
)
from .history_utils import log_user_activity


class BookViewSet(viewsets.ModelViewSet):
    """API для работы с книгами"""
    queryset = Book.objects.all().select_related('owner').prefetch_related('genres', 'reviews')
    pagination_class = BookPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['genres', 'owner']
    search_fields = ['title', 'author', 'description']
    ordering_fields = ['created_at', 'title', 'author']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BookCreateUpdateSerializer
        return BookDetailSerializer
    
    def get_permissions(self):
        """Настройка разрешений"""
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Автоматически устанавливаем владельца книги"""
        book = serializer.save(owner=self.request.user)
        log_user_activity(
            self.request.user, 
            'create_book', 
            'Book', 
            book.id, 
            f"Создана книга '{book.title}'",
            self.request
        )
    
    def perform_update(self, serializer):
        """Логируем обновление книги"""
        book = serializer.save()
        log_user_activity(
            self.request.user, 
            'update_book', 
            'Book', 
            book.id, 
            f"Обновлена книга '{book.title}'",
            self.request
        )
    
    def perform_destroy(self, instance):
        """Логируем удаление книги"""
        log_user_activity(
            self.request.user, 
            'delete_book', 
            'Book', 
            instance.id, 
            f"Удалена книга '{instance.title}'",
            self.request
        )
        super().perform_destroy(instance)
    
    def get_queryset(self):
        """Фильтрация книг"""
        queryset = super().get_queryset()
        
        # Фильтр по наличию файла
        has_file = self.request.query_params.get('has_file')
        if has_file is not None:
            if has_file.lower() == 'true':
                queryset = queryset.exclude(book_file='')
            else:
                queryset = queryset.filter(book_file='')
        
        # Фильтр по рейтингу
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__gte=float(min_rating))
        
        return queryset
    
    def destroy(self, request, *args, **kwargs):
        """Удаление книги (только владелец)"""
        book = self.get_object()
        if book.owner != request.user:
            return Response(
                {'error': 'Вы можете удалять только свои книги'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Обновление книги (только владелец)"""
        book = self.get_object()
        if book.owner != request.user:
            return Response(
                {'error': 'Вы можете редактировать только свои книги'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    # ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ @action
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Скачивание файла книги"""
        book = self.get_object()
        if not book.book_file:
            return Response(
                {'error': 'Файл книги недоступен'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            response = HttpResponse(
                book.book_file.read(), 
                content_type='application/octet-stream'
            )
            filename = f"{book.title}.{book.book_file.name.split('.')[-1]}"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            # Логируем скачивание
            log_user_activity(
                request.user, 
                'download_book', 
                'Book', 
                book.id, 
                f"Скачана книга '{book.title}'",
                request
            )
            return response
        except Exception as e:
            return Response(
                {'error': 'Ошибка при скачивании файла'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def my_books(self, request):
        """Получить книги текущего пользователя"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Необходима авторизация'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = self.get_queryset().filter(owner=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика по книгам"""
        stats = {
            'total_books': Book.objects.count(),
            'total_users': User.objects.count(),
            'total_reviews': Review.objects.count(),
            'average_rating': Review.objects.aggregate(
                avg=Avg('rating')
            )['avg'] or 0,
            'books_with_files': Book.objects.exclude(book_file='').count(),
            'most_popular_genre': Genre.objects.annotate(
                books_count=Count('book')
            ).order_by('-books_count').first().name if Genre.objects.exists() else 'Нет данных'
        }
        
        serializer = BookStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Популярные книги (с высоким рейтингом)"""
        queryset = self.get_queryset().annotate(
            avg_rating=Avg('reviews__rating'),
            reviews_count=Count('reviews')
        ).filter(
            reviews_count__gte=1
        ).order_by('-avg_rating', '-reviews_count')
        
        self.pagination_class = SmallResultsSetPagination
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BookListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = BookListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Трендовые книги (недавно добавленные с хорошими отзывами)"""
        last_month = timezone.now() - timedelta(days=30)
        
        queryset = self.get_queryset().filter(
            created_at__gte=last_month
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            reviews_count=Count('reviews')
        ).filter(
            avg_rating__gte=4.0
        ).order_by('-avg_rating', '-reviews_count')
        
        serializer = BookListSerializer(queryset[:10], many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Добавить/убрать книгу из избранного (пример)"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Необходима авторизация'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        book = self.get_object()
        
        # Здесь можно реализовать логику избранного
        # Для примера просто логируем действие
        log_user_activity(
            request.user, 
            'toggle_favorite', 
            'Book', 
            book.id, 
            f"Переключено избранное для книги '{book.title}'",
            request
        )
        
        return Response({'status': 'Избранное переключено'})
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """История изменений книги"""
        book = self.get_object()
        if book.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Нет доступа к истории этой книги'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        history = book.history.all().order_by('-history_date')[:20]
        history_data = []
        for record in history:
            history_data.append({
                'history_id': str(record.history_id),
                'history_date': record.history_date,
                'history_type': record.history_type,
                'history_change_reason': record.history_change_reason,
                'title': record.title,
                'author': record.author,
                'description': record.description[:100] + '...' if len(record.description) > 100 else record.description
            })
        return Response({
            'book_id': book.id,
            'book_title': book.title,
            'history': history_data
        })
    
    @action(detail=False, methods=['get'])
    def export_data(self, request):
        """Экспорт данных книг в JSON"""
        queryset = self.get_queryset()
        
        # Фильтрация для экспорта
        if request.user.is_authenticated:
            queryset = queryset.filter(owner=request.user)
        else:
            return Response(
                {'error': 'Необходима авторизация'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = BookListSerializer(queryset, many=True)
        
        response = HttpResponse(
            json.dumps(serializer.data, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="my_books.json"'
        
        return response


class ReviewViewSet(viewsets.ModelViewSet):
    """API для работы с отзывами"""
    queryset = Review.objects.all().select_related('user', 'book')
    serializer_class = ReviewSerializer
    pagination_class = ReviewPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['book', 'user', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Настройка разрешений"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Автоматически устанавливаем автора отзыва"""
        review = serializer.save(user=self.request.user)
        log_user_activity(
            self.request.user, 
            'create_review', 
            'Review', 
            review.id, 
            f"Создан отзыв на книгу '{review.book.title}'",
            self.request
        )
    
    def destroy(self, request, *args, **kwargs):
        """Удаление отзыва (только автор)"""
        review = self.get_object()
        if review.user != request.user:
            return Response(
                {'error': 'Вы можете удалять только свои отзывы'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Обновление отзыва (только автор)"""
        review = self.get_object()
        if review.user != request.user:
            return Response(
                {'error': 'Вы можете редактировать только свои отзывы'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    # ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ @action
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Мои отзывы"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Необходима авторизация'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Отзывы с высокими оценками"""
        queryset = self.get_queryset().filter(rating__gte=4).order_by('-rating', '-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GenreViewSet(viewsets.ModelViewSet):
    """API для работы с жанрами"""
    queryset = Genre.objects.all().annotate(books_count=Count('book'))
    serializer_class = GenreSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'books_count']
    ordering = ['name']
    
    def get_permissions(self):
        """Настройка разрешений"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    # ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ @action
    
    @action(detail=False, methods=['get'])
    def popular_genres(self, request):
        """Популярные жанры"""
        queryset = self.get_queryset().filter(books_count__gt=0).order_by('-books_count')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Книги определенного жанра"""
        genre = self.get_object()
        books = Book.objects.filter(genres=genre).select_related('owner')
        
        # Пагинация
        paginator = BookPagination()
        page = paginator.paginate_queryset(books, request)
        if page is not None:
            serializer = BookListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API для работы с пользователями (только чтение)"""
    queryset = User.objects.all().select_related('userprofile')
    serializer_class = UserSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined']
    ordering = ['username']
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получить информацию о текущем пользователе"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Необходима авторизация'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """Активность пользователя"""
        user = self.get_object()
        
        # Только свою активность или для админов
        if request.user != user and not request.user.is_staff:
            return Response(
                {'error': 'Нет доступа к активности этого пользователя'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:50]
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """API для работы с профилями пользователей"""
    queryset = UserProfile.objects.all().select_related('user')
    serializer_class = UserProfileSerializer
    pagination_class = CustomPageNumberPagination
    
    def get_permissions(self):
        """Настройка разрешений"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Работа с профилем текущего пользователя"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Необходима авторизация'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(profile, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                log_user_activity(
                    request.user, 
                    'update_profile', 
                    'UserProfile', 
                    profile.id, 
                    "Обновлен профиль пользователя",
                    request
                )
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ModelViewSet):
    """API для работы с сообщениями"""
    serializer_class = MessageSerializer
    pagination_class = MessagePagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['book', 'is_read']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь видит только свои сообщения"""
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        ).select_related('sender', 'recipient', 'book')
    
    def perform_create(self, serializer):
        """Автоматически устанавливаем отправителя"""
        message = serializer.save(sender=self.request.user)
        log_user_activity(
            self.request.user, 
            'send_message', 
            'Message', 
            message.id, 
            f"Отправлено сообщение пользователю {message.recipient.username}",
            self.request
        )
    
    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Входящие сообщения"""
        queryset = self.get_queryset().filter(recipient=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Отправленные сообщения"""
        queryset = self.get_queryset().filter(sender=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Отметить сообщение как прочитанное"""
        message = self.get_object()
        if message.recipient != request.user:
            return Response(
                {'error': 'Вы можете отмечать только свои сообщения'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_read = True
        message._change_reason = "Отмечено как прочитанное через API"
        message.save()
        
        log_user_activity(
            request.user, 
            'read_message', 
            'Message', 
            message.id, 
            f"Прочитано сообщение от {message.sender.username}",
            request
        )
        
        return Response({'status': 'Сообщение отмечено как прочитанное'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Количество непрочитанных сообщений"""
        count = self.get_queryset().filter(
            recipient=request.user, 
            is_read=False
        ).count()
        return Response({'unread_count': count})
