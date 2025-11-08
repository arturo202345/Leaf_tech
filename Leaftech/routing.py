from django.urls import path
from clasificador.consumer import VideoConsumer

websocket_urlpatterns = [
    path("ws/video/", VideoConsumer.as_asgi()),
]