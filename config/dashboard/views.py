from django.shortcuts import render
from django.http import HttpResponse

def dashboard(request):
    return HttpResponse("Welcome to my new app!")
