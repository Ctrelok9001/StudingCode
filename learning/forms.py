from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile


class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        label="Имя пользователя (логин)",
        min_length=3,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 transition-all',
            'placeholder': 'Придумайте логин (например, python_dev)',
            'autocomplete': 'username'
        })
    )
    first_name = forms.CharField(
        label="Ваше имя",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 transition-all',
            'placeholder': 'Как к вам обращаться',
        })
    )
    email = forms.EmailField(
        label="Электронная почта",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 transition-all',
            'placeholder': 'name@example.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label="Пароль",
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 transition-all',
            'placeholder': 'Минимум 6 символов',
            'autocomplete': 'new-password'
        })
    )
    password_confirm = forms.CharField(
        label="Подтверждение пароля",
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 transition-all',
            'placeholder': 'Повторите пароль',
            'autocomplete': 'new-password'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Пароли не совпадают.")

        return cleaned_data


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Логин или Email",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 transition-all',
            'placeholder': 'Введите ваш логин',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 transition-all',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        })
    )


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Имя",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 text-sm'
        })
    )
    email = forms.EmailField(
        label="Электронная почта",
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 text-sm'
        })
    )
    bio = forms.CharField(
        label="О себе",
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 text-sm',
            'placeholder': 'Расскажите немного о ваших целях в программировании'
        })
    )

    class Meta:
        model = UserProfile
        fields = ('bio',)
