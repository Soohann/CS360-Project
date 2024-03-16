from django.shortcuts import render
from django.http import HttpResponse

def homePage(request):
    return render(request, "home.html")

def bio(request):
    return render(request, 'student.html')

def blog(request):
    return render(request, 'professor.html')

def photos(request):
    return render(request, 'community.html')