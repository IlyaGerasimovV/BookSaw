from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),

    # Каталог и книги
    path('catalog/', views.book_catalog, name='book_catalog'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('book/<int:pk>/download/', views.download_book, name='download_book'),
    path('book/<int:pk>/contact/', views.contact_owner, name='contact_owner'),
    path('add-book/', views.add_book, name='add_book'),
    path('edit-book/<int:pk>/', views.edit_book, name='edit_book'),
    path('delete-book/<int:pk>/', views.delete_book, name='delete_book'),

    # Сообщения
    path('messages/', views.messages_inbox, name='messages_inbox'),
    path('message/<int:pk>/', views.message_detail, name='message_detail'),

    # Пользователи
    path('profile/', views.user_profile, name='user_profile'),
    path('register/', views.register, name='register'),

    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]
