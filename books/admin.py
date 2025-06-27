from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from django.contrib import messages
from django.core.exceptions import ValidationError
from simple_history.admin import SimpleHistoryAdmin
from import_export.admin import ImportExportModelAdmin
from .models import Book, Review, Genre, UserProfile, Message, UserActivity
from .resources import BookResource, ReviewResource, GenreResource, UserProfileResource, MessageResource


class ReviewInline(admin.TabularInline):
    """Инлайн для отзывов в админке книг"""
    model = Review
    extra = 0
    readonly_fields = ('created_at', 'rating_stars')
    fields = ('user', 'rating', 'rating_stars', 'text', 'created_at')
    
    def rating_stars(self, obj):
        """Отображение рейтинга звездочками"""
        if obj.rating:
            return "★" * obj.rating + "☆" * (5 - obj.rating)
        return "-"
    rating_stars.short_description = "Рейтинг"


class MessageInline(admin.TabularInline):
    """Инлайн для сообщений в админке книг"""
    model = Message
    extra = 0
    readonly_fields = ('created_at', 'sender_link', 'recipient_link')
    fields = ('sender_link', 'recipient_link', 'subject', 'is_read', 'created_at')
    
    def sender_link(self, obj):
        """Ссылка на отправителя"""
        if obj.sender:
            url = reverse('admin:auth_user_change', args=[obj.sender.id])
            return format_html('<a href="{}">{}</a>', url, obj.sender.username)
        return "-"
    sender_link.short_description = "Отправитель"
    
    def recipient_link(self, obj):
        """Ссылка на получателя"""
        if obj.recipient:
            url = reverse('admin:auth_user_change', args=[obj.recipient.id])
            return format_html('<a href="{}">{}</a>', url, obj.recipient.username)
        return "-"
    recipient_link.short_description = "Получатель"


@admin.register(Genre)
class GenreAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    """Админка для жанров"""
    resource_class = GenreResource
    
    list_display = ['name', 'books_count', 'created_books_link']
    search_fields = ['name']
    list_filter = ['name']
    ordering = ['name']
    
    # Настройки полей
    fields = ['name']
    
    # История
    history_list_display = ['name']
    
    def books_count(self, obj):
        """Количество книг в жанре"""
        count = obj.book_set.count()
        if count > 0:
            url = reverse('admin:books_book_changelist') + f'?genres__id__exact={obj.id}'
            return format_html('<a href="{}" style="color: green; font-weight: bold;">{}</a>', url, count)
        return format_html('<span style="color: red;">0</span>')
    books_count.short_description = 'Количество книг'
    books_count.admin_order_field = 'book_count'
    
    def created_books_link(self, obj):
        """Ссылка на создание книги с этим жанром"""
        url = reverse('admin:books_book_add') + f'?genres={obj.id}'
        return format_html('<a href="{}" class="addlink">Добавить книгу</a>', url)
    created_books_link.short_description = 'Действия'
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).annotate(
            book_count=models.Count('book')  # Изменить admin.Count на models.Count
        )


@admin.register(Book)
class BookAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    """Админка для книг"""
    resource_class = BookResource
    
    # Основные настройки отображения
    list_display = [
        'title', 'author', 'owner_link', 'genres_display', 
        'average_rating_display', 'reviews_count', 'has_file_display', 
        'created_at_short', 'book_actions'
    ]
    
    list_filter = [
        'genres', 'created_at', 'owner', 
        ('book_file', admin.EmptyFieldListFilter),
        ('cover_image', admin.EmptyFieldListFilter)
    ]
    
    search_fields = ['title', 'author', 'description', 'owner__username']
    
    filter_horizontal = ['genres']
    
    readonly_fields = ['created_at', 'updated_at', 'average_rating_display', 'file_info']
    
    # Группировка полей
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'author', 'description')
        }),
        ('Категоризация', {
            'fields': ('genres',),
            'classes': ('wide',)
        }),
        ('Файлы', {
            'fields': ('cover_image', 'book_file', 'file_info'),
            'classes': ('collapse',)
        }),
        ('Владелец и даты', {
            'fields': ('owner', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': ('average_rating_display',),
            'classes': ('collapse',)
        })
    )
    
    # Инлайны
    inlines = [ReviewInline, MessageInline]
    
    # История
    history_list_display = ['title', 'author', 'owner']
    
    # Настройки списка
    list_per_page = 25
    list_max_show_all = 100
    
    def owner_link(self, obj):
        """Ссылка на владельца книги"""
        url = reverse('admin:auth_user_change', args=[obj.owner.id])
        return format_html(
            '<a href="{}" style="color: blue;">{}</a>', 
            url, 
            obj.owner.get_full_name() or obj.owner.username
        )
    owner_link.short_description = 'Владелец'
    owner_link.admin_order_field = 'owner__username'
    
    def genres_display(self, obj):
        """Отображение жанров"""
        genres = obj.genres.all()[:3]  # Показываем только первые 3
        if genres:
            genre_links = []
            for genre in genres:
                url = reverse('admin:books_genre_change', args=[genre.id])
                genre_links.append(f'<a href="{url}">{genre.name}</a>')
            result = ', '.join(genre_links)
            if obj.genres.count() > 3:
                result += f' <span style="color: gray;">+{obj.genres.count() - 3}</span>'
            return mark_safe(result)
        return "-"
    genres_display.short_description = 'Жанры'
    
    def average_rating_display(self, obj):
        """Отображение среднего рейтинга"""
        rating = obj.average_rating()
        if rating > 0:
            stars = "★" * int(rating) + "☆" * (5 - int(rating))
            color = "green" if rating >= 4 else "orange" if rating >= 3 else "red"
            return format_html(
                '<span style="color: {};">{} ({})</span>', 
                color, stars, rating
            )
        return format_html('<span style="color: gray;">Нет оценок</span>')
    average_rating_display.short_description = 'Рейтинг'
    
    def reviews_count(self, obj):
        """Количество отзывов"""
        count = obj.reviews.count()
        if count > 0:
            url = reverse('admin:books_review_changelist') + f'?book__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"
    reviews_count.short_description = 'Отзывы'

    def has_file_boolean(self, obj):
        """Наличие файла книги (boolean для сортировки)"""
        return bool(obj.book_file)
    has_file_boolean.boolean = True
    has_file_boolean.short_description = 'Файл (bool)'

    def has_file_display(self, obj):
        """Наличие файла книги"""
        if obj.book_file:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Есть</span>'
            )
        return format_html('<span style="color: red;">✗ Нет</span>')
    has_file_display.short_description = 'Файл'
    
    def created_at_short(self, obj):
        """Краткая дата создания"""
        return obj.created_at.strftime('%d.%m.%Y')
    created_at_short.short_description = 'Создана'
    created_at_short.admin_order_field = 'created_at'
    
    def file_info(self, obj):
        """Информация о файле"""
        if obj.book_file:
            try:
                size = obj.book_file.size
                size_mb = round(size / (1024 * 1024), 2)
                return f"Размер: {size_mb} МБ"
            except:
                return "Файл недоступен"
        return "Файл не загружен"
    file_info.short_description = 'Информация о файле'
    
    def book_actions(self, obj):
        """Дополнительные действия"""
        actions = []
        
        # Ссылка на просмотр на сайте
        view_url = obj.get_absolute_url()
        actions.append(f'<a href="{view_url}" target="_blank" title="Посмотреть на сайте">👁</a>')
        
        # Ссылка на добавление отзыва
        review_url = reverse('admin:books_review_add') + f'?book={obj.id}'
        actions.append(f'<a href="{review_url}" title="Добавить отзыв">📝</a>')
        
        return mark_safe(' | '.join(actions))
    book_actions.short_description = 'Действия'
    
    def save_model(self, request, obj, form, change):
        """Добавляем причину изменения и обрабатываем ошибки валидации"""
        try:
            if change:
                obj._change_reason = f"Изменено администратором {request.user.username}"
            else:
                obj._change_reason = f"Создано администратором {request.user.username}"
            super().save_model(request, obj, form, change)
            if change:
                messages.success(request, f'Книга "{obj.title}" успешно обновлена.')
            else:
                messages.success(request, f'Книга "{obj.title}" успешно создана.')
        except ValidationError as e:
            messages.error(request, f'Ошибка валидации: {e.message}')
            raise
        except Exception as e:
            messages.error(request, f'Произошла ошибка при сохранении: {str(e)}')
            raise


@admin.register(Review)
class ReviewAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    """Админка для отзывов"""
    resource_class = ReviewResource
    
    list_display = [
        'book_link', 'user_link', 'rating_display', 
        'text_preview', 'created_at_short'
    ]
    
    list_filter = ['rating', 'created_at', 'book__genres']
    
    search_fields = ['book__title', 'user__username', 'text']
    
    readonly_fields = ['created_at']
    
    # Группировка полей
    fieldsets = (
        ('Отзыв', {
            'fields': ('book', 'user', 'rating', 'text')
        }),
        ('Метаданные', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    # История
    history_list_display = ['book', 'user', 'rating']
    
    def book_link(self, obj):
        """Ссылка на книгу"""
        url = reverse('admin:books_book_change', args=[obj.book.id])
        return format_html('<a href="{}">{}</a>', url, obj.book.title)
    book_link.short_description = 'Книга'
    book_link.admin_order_field = 'book__title'
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user__username'
    
    def rating_display(self, obj):
        """Отображение рейтинга"""
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        color = "green" if obj.rating >= 4 else "orange" if obj.rating >= 3 else "red"
        return format_html('<span style="color: {};">{}</span>', color, stars)
    rating_display.short_description = 'Рейтинг'
    rating_display.admin_order_field = 'rating'
    
    def text_preview(self, obj):
        """Превью текста отзыва"""
        if len(obj.text) > 50:
            return obj.text[:50] + "..."
        return obj.text
    text_preview.short_description = 'Текст'
    
    def created_at_short(self, obj):
        """Краткая дата создания"""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_short.short_description = 'Дата'
    created_at_short.admin_order_field = 'created_at'


@admin.register(UserProfile)
class UserProfileAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    """Админка для профилей пользователей"""
    resource_class = UserProfileResource
    
    list_display = [
        'user_link', 'full_name', 'location', 'has_avatar', 
        'books_count', 'reviews_count', 'contact_info'
    ]
    
    list_filter = [
        'location', 
        ('avatar', admin.EmptyFieldListFilter),
        ('phone', admin.EmptyFieldListFilter)
    ]
    
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'location']
    
    # Группировка полей
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Личная информация', {
            'fields': ('bio', 'location', 'birth_date', 'avatar')
        }),
        ('Контакты', {
            'fields': ('phone', 'telegram'),
            'classes': ('collapse',)
        })
    )
    
    # История
    history_list_display = ['user', 'location']
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user__username'
    
    def full_name(self, obj):
        """Полное имя пользователя"""
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Полное имя'

    def has_avatar_boolean(self, obj):
        """Наличие аватара (boolean для сортировки)"""
        return bool(obj.avatar)

    has_avatar_boolean.boolean = True
    has_avatar_boolean.short_description = 'Аватар (bool)'

    def has_avatar(self, obj):
        """Наличие аватара"""
        if obj.avatar:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_avatar.short_description = 'Аватар'
    
    def books_count(self, obj):
        """Количество книг пользователя"""
        count = obj.user.book_set.count()
        if count > 0:
            url = reverse('admin:books_book_changelist') + f'?owner__id__exact={obj.user.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"
    books_count.short_description = 'Книги'
    
    def reviews_count(self, obj):
        """Количество отзывов пользователя"""
        count = obj.user.review_set.count()
        if count > 0:
            url = reverse('admin:books_review_changelist') + f'?user__id__exact={obj.user.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"
    reviews_count.short_description = 'Отзывы'
    
    def contact_info(self, obj):
        """Контактная информация"""
        contacts = []
        if obj.phone:
            contacts.append(f"📞 {obj.phone}")
        if obj.telegram:
            contacts.append(f"📱 {obj.telegram}")
        return " | ".join(contacts) if contacts else "-"
    contact_info.short_description = 'Контакты'


@admin.register(Message)
class MessageAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    """Админка для сообщений"""
    resource_class = MessageResource
    
    list_display = [
        'sender_link', 'recipient_link', 'book_link', 
        'subject', 'is_read_display', 'created_at_short'
    ]
    
    list_filter = ['is_read', 'created_at', 'book__genres']
    
    search_fields = ['sender__username', 'recipient__username', 'subject', 'message']
    
    readonly_fields = ['created_at']
    
    # Группировка полей
    fieldsets = (
        ('Участники', {
            'fields': ('sender', 'recipient', 'book')
        }),
        ('Сообщение', {
            'fields': ('subject', 'message', 'is_read')
        }),
        ('Метаданные', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    # История
    history_list_display = ['sender', 'recipient', 'subject', 'is_read']
    
    def sender_link(self, obj):
        """Ссылка на отправителя"""
        url = reverse('admin:auth_user_change', args=[obj.sender.id])
        return format_html('<a href="{}">{}</a>', url, obj.sender.username)
    sender_link.short_description = 'Отправитель'
    sender_link.admin_order_field = 'sender__username'
    
    def recipient_link(self, obj):
        """Ссылка на получателя"""
        url = reverse('admin:auth_user_change', args=[obj.recipient.id])
        return format_html('<a href="{}">{}</a>', url, obj.recipient.username)
    recipient_link.short_description = 'Получатель'
    recipient_link.admin_order_field = 'recipient__username'
    
    def book_link(self, obj):
        """Ссылка на книгу"""
        url = reverse('admin:books_book_change', args=[obj.book.id])
        return format_html('<a href="{}">{}</a>', url, obj.book.title)
    book_link.short_description = 'Книга'
    book_link.admin_order_field = 'book__title'

    def is_read_boolean(self, obj):
        """Статус прочтения (boolean для сортировки)"""
        return obj.is_read
    is_read_boolean.boolean = True
    is_read_boolean.short_description = 'Прочитано (bool)'


    def is_read_display(self, obj):
        """Статус прочтения"""
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Прочитано</span>')
        return format_html('<span style="color: red;">✗ Не прочитано</span>')
    is_read_display.short_description = 'Статус'

    
    def created_at_short(self, obj):
        """Краткая дата создания"""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_short.short_description = 'Дата'
    created_at_short.admin_order_field = 'created_at'


@admin.register(UserActivity)
class UserActivityAdmin(SimpleHistoryAdmin):
    """Админка для активности пользователей"""
    
    list_display = [
        'user_link', 'action_display', 'object_info', 
        'ip_address', 'timestamp_short'
    ]
    
    list_filter = ['action', 'object_type', 'timestamp']
    
    search_fields = ['user__username', 'description', 'ip_address']
    
    readonly_fields = ['timestamp', 'user_agent_short']
    
    # Группировка полей
    fieldsets = (
        ('Активность', {
            'fields': ('user', 'action', 'object_type', 'object_id', 'description')
        }),
        ('Техническая информация', {
            'fields': ('ip_address', 'user_agent_short', 'timestamp'),
            'classes': ('collapse',)
        })
    )
    
    # История
    history_list_display = ['user', 'action', 'object_type']
    
    def has_add_permission(self, request):
        """Запрещаем создание активности через админку"""
        return False
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user__username'
    
    def action_display(self, obj):
        """Отображение действия"""
        action_colors = {
            'create_book': 'green',
            'update_book': 'blue',
            'delete_book': 'red',
            'create_review': 'purple',
            'send_message': 'orange',
        }
        color = action_colors.get(obj.action, 'black')
        return format_html(
            '<span style="color: {};">{}</span>', 
            color, 
            obj.get_action_display()
        )
    action_display.short_description = 'Действие'
    action_display.admin_order_field = 'action'
    
    def object_info(self, obj):
        """Информация об объекте"""
        if obj.object_type and obj.object_id:
            return f"{obj.object_type} #{obj.object_id}"
        return "-"
    object_info.short_description = 'Объект'
    
    def timestamp_short(self, obj):
        """Краткое время"""
        return obj.timestamp.strftime('%d.%m.%Y %H:%M')
    timestamp_short.short_description = 'Время'
    timestamp_short.admin_order_field = 'timestamp'
    
    def user_agent_short(self, obj):
        """Краткий User Agent"""
        if obj.user_agent:
            return obj.user_agent[:100] + "..." if len(obj.user_agent) > 100 else obj.user_agent
        return "-"
    user_agent_short.short_description = 'User Agent'
