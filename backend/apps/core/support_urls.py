from django.urls import path

from .views import SupportChatApiView

urlpatterns = [
    path("api/", SupportChatApiView.as_view(), name="support_chat_api"),
]
