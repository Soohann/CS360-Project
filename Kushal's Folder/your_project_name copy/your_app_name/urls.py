from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('student_dashboard.html', views.student_dashboard, name='student_dashboard'),
]

