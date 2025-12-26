from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings


def index(request):
    context = {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
        'staff_whatsapp': settings.STAFF_WHATSAPP,
    }
    return render(request, "website/index.html", context)


def about(request):
    context = {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
    }
    return render(request, "website/about.html", context)


def courses(request):
    context = {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
    }
    return render(request, "website/courses.html", context)


def cpa(request):
    context = {
        'staff_whatsapp': settings.STAFF_WHATSAPP,
        'cpa_start_date': settings.CPA_START_DATE,
        'cpa_duration': settings.CPA_DURATION,
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
    }
    return render(request, "website/cpa.html", context)

def sim(request):
    context = {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
    }
    return render(request, "website/sim.html", context)

def privacy(request):
    context = {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
    }
    return render(request, "website/privacy.html", context)