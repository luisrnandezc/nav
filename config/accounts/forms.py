from django import forms
from django.contrib.auth.forms import PasswordChangeForm


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-field', 'placeholder': 'Username'}), label=False)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-field', 'placeholder': 'Password'}), label=False)


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={
            'class': 'password-field',
        })
    )
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'password-field',
        })
    )
    new_password2 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'password-field',
        })
    )