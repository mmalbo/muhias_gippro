from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'width:100%'}),
        required=True,
        label='Responsabilidad:'
    )
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=None,
        required=True
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=None,
        required=True
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden")
        validate_password(password2)
        return password2

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'groups', 'password1', 'password2', 'is_active')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'right:92%'}),

        }
        labels = {
            'first_name': 'Nombre:',
            'last_name': 'Apellidos:',
            'username': 'Usuario:',
            'email': 'Correo:',
            'is_active': 'Activo:',
        }


class CustomUserChangeForm(UserChangeForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'width:100%'}),
        required=True,
        label='Responsabilidad:'
    )
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=None,
        required=True
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=None,
        required=True
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden")
        validate_password(password2)
        return password2

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'groups', 'password1', 'password2', 'is_active')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'right:92%'}),

        }
        labels = {
            'first_name': 'Nombre:',
            'last_name': 'Apellidos:',
            'username': 'Usuario:',
            'email': 'Correo:',
            'is_active': 'Activo:',
        }
