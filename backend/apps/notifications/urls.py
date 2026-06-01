from django.urls import path

from .views import MarkAllReadApiView, MarkReadApiView, NotificationListApiView

app_name = "notifications"

urlpatterns = [
    path("", NotificationListApiView.as_view(), name="list"),
    path("mark-all-read/", MarkAllReadApiView.as_view(), name="mark_all_read"),
    path("<int:pk>/read/", MarkReadApiView.as_view(), name="mark_read"),
]
