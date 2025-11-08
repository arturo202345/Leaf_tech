import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import Leaftech.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Leaftech.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(Leaftech.routing.websocket_urlpatterns),
})