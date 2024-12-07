from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    user = request.user
    context = {
        'username': user.username,
        'email': user.email,
    }
    return render(request, "dashboard/dashboard.html", context)
