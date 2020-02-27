from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:room_id>/<str:user_id>/', consumers.ChatConsumer),
]