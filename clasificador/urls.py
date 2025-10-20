from django.urls import path
from clasificador.infraestructure import django_views as views

urlpatterns = [
    path('', views.index, name='index'),           # Página principal
    path('video_feed/', views.video_feed, name='video_feed'),
    path('page1/', views.page_1, name='page1'),
    path('get_last_result/', views.get_last_result, name='get_last_result'),
    path('get_plant_data/', views.get_plant_data, name='get_plant_data'),
]