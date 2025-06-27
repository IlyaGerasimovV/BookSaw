from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Book, Review, Genre, UserProfile
from .forms import BookForm, ReviewForm, UserProfileForm

def home(request):
    """Главная страница"""
    recent_books = Book.objects.all()[:6]  # Последние 6 книг
    context = {
        'recent_books': recent_books,
    }
    return render(request, 'books/home.html', context)

def book_catalog(request):
    """Каталог книг"""
    books = Book.objects.all()
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
        'selected_genre': genre_filter,
    }
    return render(request, 'books/catalog.html', context)

def book_detail(request, pk):
    """Страница книги"""
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.all()
    
    # Форма для добавления отзыва
    review_form = None
    if request.user.is_authenticated:
        if request.method == 'POST':
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.book = book
                review.user = request.user
                review.save()
                messages.success(request, 'Отзыв успешно добавлен!')
                return redirect('book_detail', pk=book.pk)
        else:
            # Проверяем, не оставлял ли пользователь уже отзыв
            existing_review = reviews.filter(user=request.user).first()
            if not existing_review:
                review_form = ReviewForm()
    
    context = {
        'book': book,
        'reviews': reviews,
        'review_form': review_form,
        'average_rating': book.average_rating(),
    }
    return render(request, 'books/book_detail.html', context)

@login_required
def user_profile(request):
    """Личный кабинет пользователя"""
    user_books = Book.objects.filter(owner=request.user)
    user_reviews = Review.objects.filter(user=request.user)
    
    # Получаем или создаем профиль пользователя
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user_books': user_books,
        'user_reviews': user_reviews,
        'profile': profile,
    }
    return render(request, 'books/profile.html', context)

@login_required
def add_book(request):
    """Добавление новой книги"""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.owner = request.user
            book.save()
            form.save_m2m()  # Сохраняем ManyToMany поля
            messages.success(request, 'Книга успешно добавлена!')
            return redirect('user_profile')
    else:
        form = BookForm()
    
    return render(request, 'books/add_book.html', {'form': form})

@login_required
def edit_book(request, pk):
    """Редактирование книги"""
    book = get_object_or_404(Book, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Книга успешно обновлена!')
            return redirect('user_profile')
    else:
        form = BookForm(instance=book)
    
    return render(request, 'books/edit_book.html', {'form': form, 'book': book})

@login_required
def delete_book(request, pk):
    """Удаление книги"""
    book = get_object_or_404(Book, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Книга успешно удалена!')
        return redirect('user_profile')
    
    return render(request, 'books/delete_book.html', {'book': book})

def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
