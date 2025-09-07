from django.contrib import admin
from django.urls import path
from quiz import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('upload/', views.upload_countries, name='upload'),
    path('countries/', views.countries_list, name='countries_list'),
    path('start/', views.start_quiz, name='start'),
    path('q/', views.question, name='question'),
    path('results/', views.results, name='results'),
]
