from django.urls import path
from clasificador.infraestructure import django_views as views

urlpatterns = [
    path('', views.index, name='index'),           # Página principal
    path('video_feed/', views.video_feed, name='video_feed'),
]