from django.urls import path

from .views import FavoriteListView, FavoriteToggleView

app_name = "favorites"

urlpatterns = [
    path("", FavoriteListView.as_view(), name="list"),
    path("toggle/<int:product_id>/", FavoriteToggleView.as_view(), name="toggle"),
]
