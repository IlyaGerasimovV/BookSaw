from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    BookViewSet, ReviewViewSet, GenreViewSet, 
    UserViewSet, UserProfileViewSet, MessageViewSet
)

# Создаем роутер для API
router = DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    # API маршруты
    path('', include(router.urls)),
    
    # Аутентификация для API
    path('auth/', include('rest_framework.urls')),
]
