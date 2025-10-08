from django.urls import path
from .consumers import *

websocket_urlpatterns = [
    # path('ws/test/', EchoBroadcastConsumer.as_asgi()),
]