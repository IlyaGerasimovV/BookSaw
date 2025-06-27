from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta
import os
from .models import Book, Review, Genre, UserProfile, Message
from .forms import BookForm, ReviewForm, UserProfileForm, CustomUserCreationForm, MessageForm


def home(request):

    recent_books = Book.objects.select_related('owner').prefetch_related('genres').order_by('-created_at')[:6]

    popular_books = Book.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        reviews_count=Count('reviews')
    ).filter(
        reviews_count__gt=0
    ).order_by('-avg_rating', '-reviews_count')[:5]

    total_books = Book.objects.count()
    total_users = User.objects.count()
    total_reviews = Review.objects.count()

    context = {
        'recent_books': recent_books,
        'popular_books': popular_books,
        'total_books': total_books,
        'total_users': total_users,
        'total_reviews': total_reviews,
    }
    return render(request, 'books/home.html', context)


def book_catalog(request):
    """Каталог книг"""
    books = Book.objects.all().select_related('owner').prefetch_related('genres')
    genres = Genre.objects.all()

    # Поиск
    search_query = request.GET.get('search')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query)
        )

    # Фильтр по жанру
    genre_filter = request.GET.get('genre')
    if genre_filter:
        books = books.filter(genres__id=genre_filter)

    # Пагинация
    paginator = Paginator(books, 12)  # 12 книг на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'genres': genres,
        'search_query': search_query,
        'selected_genre': int(genre_filter) if genre_filter else None,
    }
    return render(request, 'books/catalog.html', context)


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.all().select_related('user')
    # Форма для добавления отзыва
    review_form = None
    user_review = None
    if request.user.is_authenticated:
        # Проверяем, не оставлял ли пользователь уже отзыв
        user_review = reviews.filter(user=request.user).first()
        if request.method == 'POST' and not user_review:
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.book = book
                review.user = request.user
                review.save()
                messages.success(request, 'Отзыв успешно добавлен!')
                return redirect('book_detail', pk=book.pk)
        elif not user_review:
            review_form = ReviewForm()
    context = {
        'book': book,
        'reviews': reviews,
        'review_form': review_form,
        'user_review': user_review,
        'average_rating': book.average_rating(),
    }
    return render(request, 'books/book_detail.html', context)


@login_required
def add_book(request):
    """Добавление новой книги"""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                book = form.save(commit=False)
                book.owner = request.user
                book.save()
                form.save_m2m()  # Сохраняем many-to-many отношения
                messages.success(request, 'Книга успешно добавлена!')
                return redirect('book_detail', pk=book.pk)
            except ValidationError as e:
                messages.error(request, f'Ошибка валидации: {e.message}')
            except Exception as e:
                messages.error(request, f'Произошла ошибка при сохранении: {str(e)}')
    else:
        form = BookForm()

    return render(request, 'books/add_book.html', {
        'form': form,
        'title': 'Добавить книгу'
    })


@login_required
def edit_book(request, pk):
    """Редактирование книги"""
    book = get_object_or_404(Book, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            try:
                book = form.save()
                messages.success(request, 'Книга успешно обновлена!')
                return redirect('book_detail', pk=book.pk)
            except ValidationError as e:
                messages.error(request, f'Ошибка валидации: {e.message}')
            except Exception as e:
                messages.error(request, f'Произошла ошибка при обновлении: {str(e)}')
    else:
        form = BookForm(instance=book)

    return render(request, 'books/edit_book.html', {
        'form': form,
        'book': book,
        'title': 'Редактировать книгу'
    })


@login_required
def delete_book(request, pk):
    """Удаление книги"""
    book = get_object_or_404(Book, pk=pk, owner=request.user)

    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Книга успешно удалена!')
        return redirect('user_profile')

    return render(request, 'books/delete_book.html', {'book': book})


@login_required
def download_book(request, pk):
    """Скачивание файла книги"""
    book = get_object_or_404(Book, pk=pk)

    if not book.book_file:
        messages.error(request, 'Файл книги недоступен для скачивания.')
        return redirect('book_detail', pk=book.pk)

    try:
        response = HttpResponse(book.book_file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{book.title}.{book.book_file.name.split(".")[-1]}"'
        return response
    except Exception as e:
        messages.error(request, 'Ошибка при скачивании файла.')
        return redirect('book_detail', pk=book.pk)


@login_required
def contact_owner(request, pk):
    """Связаться с владельцем книги"""
    book = get_object_or_404(Book, pk=pk)

    if request.user == book.owner:
        messages.error(request, 'Вы не можете отправить сообщение самому себе.')
        return redirect('book_detail', pk=book.pk)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = book.owner
            message.book = book
            message.save()
            messages.success(request, 'Сообщение отправлено!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = MessageForm(initial={
            'subject': f'Интерес к книге "{book.title}"'
        })

    context = {
        'form': form,
        'book': book,
    }
    return render(request, 'books/contact_owner.html', context)


@login_required
def messages_inbox(request):
    """Входящие сообщения"""
    messages_list = Message.objects.filter(recipient=request.user).select_related('sender', 'book')

    # Пагинация
    paginator = Paginator(messages_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'books/messages_inbox.html', context)


@login_required
def message_detail(request, pk):
    """Просмотр сообщения"""
    message = get_object_or_404(Message, pk=pk)

    # Проверяем, что пользователь имеет право просматривать сообщение
    if request.user != message.sender and request.user != message.recipient:
        raise Http404

    # Отмечаем сообщение как прочитанное
    if request.user == message.recipient and not message.is_read:
        message.is_read = True
        message.save()

    context = {
        'message': message,
    }
    return render(request, 'books/message_detail.html', context)


@login_required
def user_profile(request):
    """Личный кабинет пользователя"""
    user_books = Book.objects.filter(owner=request.user).prefetch_related('genres')
    user_reviews = Review.objects.filter(user=request.user).select_related('book')
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()

    # Получаем или создаем профиль пользователя
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Обработка обновления профиля
    if request.method == 'POST':
        # Обновляем основную информацию пользователя
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()

        # Обновляем профиль
        profile.bio = request.POST.get('bio', '')
        profile.location = request.POST.get('location', '')
        profile.phone = request.POST.get('phone', '')
        profile.telegram = request.POST.get('telegram', '')

        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']

        profile.save()
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('user_profile')

    context = {
        'user_books': user_books,
        'user_reviews': user_reviews,
        'profile': profile,
        'unread_messages': unread_messages,
    }
    return render(request, 'books/profile.html', context)


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем профиль пользователя
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# AJAX валидация для проверки названия в реальном времени
def validate_title_ajax(request):
    """AJAX валидация названия книги"""
    if request.method == 'GET':
        title = request.GET.get('title', '').strip()

        try:
            # Создаем временный объект для валидации
            temp_book = Book(title=title)
            temp_book.clean_title()
            return JsonResponse({'valid': True, 'message': 'Название корректно'})
        except ValidationError as e:
            return JsonResponse({'valid': False, 'message': str(e.message)})

    return JsonResponse({'valid': False, 'message': 'Неверный запрос'})
