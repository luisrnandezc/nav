from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings


def index(request):
    return render(request, "website/index.html")


def about(request):
    return render(request, "website/about.html")


def courses(request):
    return render(request, "website/courses.html")


def cpa(request):
    context = {
        'staff_whatsapp': settings.STAFF_WHATSAPP,
        'cpa_start_date': settings.CPA_START_DATE,
    }
    return render(request, "website/cpa.html", context)

def sim(request):
    return render(request, "website/sim.html")

def privacy(request):
    return render(request, "website/privacy.html")