from django.urls import path
from .api import api
from .consumer import JobConsumer

urlpatterns = [
    path('api/v1/', api.urls)
]

websocket_urlpatterns = [
    path("ws/live_job_updates/", JobConsumer.as_asgi())
]