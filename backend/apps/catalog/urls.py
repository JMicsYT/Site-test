from django.urls import path

from .views import CatalogListView, CategoryListView, ProductDetailView
from .views_review import ReviewCreateView


urlpatterns = [
    path("", CatalogListView.as_view(), name="list"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("<slug:slug>/review/", ReviewCreateView.as_view(), name="review_create"),
    path("<slug:slug>/", ProductDetailView.as_view(), name="detail"),
]

