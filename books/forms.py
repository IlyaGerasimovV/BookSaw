from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Book, Review, UserProfile, Genre, Message

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'genres', 'description', 'cover_image', 'book_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'genres': forms.CheckboxSelectMultiple(),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'book_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.epub,.fb2,.txt,.doc,.docx'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')

        if not title:
            raise ValidationError('Название книги обязательно для заполнения.')

        # Убираем лишние пробелы
        title = title.strip()

        if not title:
            raise ValidationError('Название книги не может состоять только из пробелов.')

        if len(title) < 2:
            raise ValidationError('Название книги должно содержать минимум 2 символа.')

        if len(title) > 200:
            raise ValidationError('Название книги не должно превышать 200 символов.')

        return title

    def save(self, commit=True):
        """Переопределяем save для установки владельца"""
        book = super().save(commit=False)
        if commit:
            book.save()
            # Сохраняем many-to-many отношения
            self.save_m2m()
        return book

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Поделитесь своими впечатлениями о книге...'}),
            'rating': forms.Select(
                choices=[(i, f'{i} звезд{"а" if i in [2,3,4] else ""}') for i in range(1, 6)],
                attrs={'class': 'form-control'}
            ),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'birth_date', 'avatar', 'phone', 'telegram']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Тема сообщения'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Ваше сообщение...'}),
        }
