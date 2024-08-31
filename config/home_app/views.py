from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return render(request, "home_app/index.html")


def courses(request):
    return render(request, "home_app/courses.html")
