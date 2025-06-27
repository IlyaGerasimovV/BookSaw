"""Утилиты для работы с историей изменений"""
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Book, Review, UserProfile, Message, UserActivity


def log_user_activity(user, action, object_type=None, object_id=None, 
                     description=None, request=None):
    """Логирование активности пользователя"""
    activity_data = {
        'user': user,
        'action': action,
        'object_type': object_type,
        'object_id': object_id,
        'description': description,
    }
    
    if request:
        # Получаем IP адрес
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        activity_data['ip_address'] = ip
        activity_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
    
    return UserActivity.objects.create(**activity_data)


def get_user_activity_summary(user, days=30):
    """Получить сводку активности пользователя за период"""
    since = timezone.now() - timedelta(days=days)
    activities = UserActivity.objects.filter(
        user=user,
        timestamp__gte=since
    ).values('action').distinct()
    
    summary = {}
    for activity in activities:
        action = activity['action']
        count = UserActivity.objects.filter(
            user=user,
            action=action,
            timestamp__gte=since
        ).count()
        summary[action] = count
    
    return summary


def get_object_change_history(obj, limit=10):
    """Получить историю изменений объекта"""
    if hasattr(obj, 'history'):
        return obj.history.all().order_by('-history_date')[:limit]
    return []


def get_recent_changes(model_class, days=7, limit=50):
    """Получить недавние изменения по модели"""
    since = timezone.now() - timedelta(days=days)
    
    if hasattr(model_class, 'history'):
        return model_class.history.filter(
            history_date__gte=since
        ).order_by('-history_date')[:limit]
    return []


def compare_object_versions(obj, version1_id, version2_id):
    """Сравнить две версии объекта"""
    if not hasattr(obj, 'history'):
        return None
    
    try:
        version1 = obj.history.get(history_id=version1_id)
        version2 = obj.history.get(history_id=version2_id)
        
        changes = []
        for field in obj._meta.fields:
            field_name = field.name
            if field_name in ['id', 'history_id', 'history_date', 'history_change_reason', 'history_type']:
                continue
                
            val1 = getattr(version1, field_name, None)
            val2 = getattr(version2, field_name, None)
            
            if val1 != val2:
                changes.append({
                    'field': field_name,
                    'old_value': val1,
                    'new_value': val2,
                    'field_verbose_name': field.verbose_name
                })
        
        return {
            'version1': version1,
            'version2': version2,
            'changes': changes
        }
    except:
        return None


def get_system_activity_stats(days=30):
    """Получить статистику активности системы"""
    since = timezone.now() - timedelta(days=days)
    
    stats = {
        'total_activities': UserActivity.objects.filter(timestamp__gte=since).count(),
        'active_users': UserActivity.objects.filter(timestamp__gte=since).values('user').distinct().count(),
        'books_created': UserActivity.objects.filter(action='create_book', timestamp__gte=since).count(),
        'reviews_created': UserActivity.objects.filter(action='create_review', timestamp__gte=since).count(),
        'messages_sent': UserActivity.objects.filter(action='send_message', timestamp__gte=since).count(),
    }
    
    # Активность по дням
    daily_stats = []
    for i in range(days):
        day = timezone.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_activities = UserActivity.objects.filter(
            timestamp__gte=day_start,
            timestamp__lt=day_end
        ).count()
        
        daily_stats.append({
            'date': day_start.date(),
            'activities': day_activities
        })
    
    stats['daily_stats'] = daily_stats
    return stats


def restore_object_version(obj, history_id):
    """Восстановить объект до определенной версии"""
    if not hasattr(obj, 'history'):
        return False
    
    try:
        historical_obj = obj.history.get(history_id=history_id)
        
        # Копируем все поля кроме служебных
        for field in obj._meta.fields:
            field_name = field.name
            if field_name not in ['id', 'created_at']:
                setattr(obj, field_name, getattr(historical_obj, field_name))
        
        obj._change_reason = f"Восстановлено до версии {history_id}"
        obj.save()
        return True
    except:
        return False


def get_user_changes_timeline(user, days=30):
    """Получить временную линию изменений пользователя"""
    since = timezone.now() - timedelta(days=days)
    
    # Собираем все изменения пользователя
    changes = []
    
    # Изменения книг
    user_books = Book.objects.filter(owner=user)
    for book in user_books:
        book_history = book.history.filter(history_date__gte=since)
        for hist in book_history:
            changes.append({
                'date': hist.history_date,
                'type': 'book',
                'action': hist.history_type,
                'object': book,
                'history': hist,
                'description': f"{hist.get_history_type_display()} книгу '{book.title}'"
            })
    
    # Изменения отзывов
    user_reviews = Review.objects.filter(user=user)
    for review in user_reviews:
        review_history = review.history.filter(history_date__gte=since)
        for hist in review_history:
            changes.append({
                'date': hist.history_date,
                'type': 'review',
                'action': hist.history_type,
                'object': review,
                'history': hist,
                'description': f"{hist.get_history_type_display()} отзыв на '{review.book.title}'"
            })
    
    # Изменения профиля
    try:
        profile = user.userprofile
        profile_history = profile.history.filter(history_date__gte=since)
        for hist in profile_history:
            changes.append({
                'date': hist.history_date,
                'type': 'profile',
                'action': hist.history_type,
                'object': profile,
                'history': hist,
                'description': f"{hist.get_history_type_display()} профиль"
            })
    except:
        pass
    
    # Сортируем по дате
    changes.sort(key=lambda x: x['date'], reverse=True)
    return changes
