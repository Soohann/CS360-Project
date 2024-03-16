from django.shortcuts import render

# Define your views here
def home(request):
    return render(request, 'home.html')

from django.shortcuts import render

def student_dashboard(request):
    # Your view logic goes here
    return render(request, 'student_dashboard.html')
