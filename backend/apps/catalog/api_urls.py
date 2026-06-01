from django.urls import path
from rest_framework import routers

from .views import CategoryViewSet, ProductViewSet
from .views_search import AutocompleteApiView


router = routers.DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")

urlpatterns = [
    path("autocomplete/", AutocompleteApiView.as_view(), name="autocomplete"),
] + router.urls

