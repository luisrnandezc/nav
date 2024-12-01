from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(label="Username", max_length=16, 
                               widget=forms.TextInput(attrs={'placeholder': 'Username',  'class': 'form-field'}))
    password = forms.CharField(label="Password", max_length=16, 
                               widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-field'}))