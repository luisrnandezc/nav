from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render
from .forms import LoginForm
from django.contrib.auth.views import PasswordChangeView
from .forms import CustomPasswordChangeForm
from django.contrib.auth.password_validation import password_validators_help_texts
from django.contrib.auth import logout
from django.shortcuts import redirect


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('dashboard:dashboard')
                else:
                    messages.error(request, 'Cuenta inactiva.')
            else:
                messages.error(request, 'Credenciales inválidas.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return render(request, 'accounts/logout.html')


class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'registration/password_change_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['password_validators_help_texts'] = password_validators_help_texts()
        return context

