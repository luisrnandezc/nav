from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return render(request, "website/index.html")


def about(request):
    return render(request, "website/about.html")


def courses(request):
    return render(request, "website/courses.html")


def cpa(request):
    return render(request, "website/cpa.html")

def sim(request):
    return render(request, "website/sim.html")