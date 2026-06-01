from django.urls import path

from .views import (
    CategoriesView,
    CategoryEditView,
    DashboardView,
    OrderDetailView,
    OrderEditView,
    OrdersExportView,
    OrdersView,
    ProductDeleteDigitalView,
    ProductDeleteMediaView,
    ProductDeleteView,
    ProductEditView,
    ProductsView,
    ReviewModerateView,
    ReviewsView,
    SecurityLogView,
    SettingsView,
    SupportTicketDetailView,
    SupportTicketsView,
    UserEditView,
    UsersView,
)


urlpatterns = [
    path("", DashboardView.as_view(), name="index"),
    path("products/", ProductsView.as_view(), name="products"),
    path("products/new/", ProductEditView.as_view(), name="product_new"),
    path("products/<int:pk>/", ProductEditView.as_view(), name="product_edit"),
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"),
    path(
        "products/<int:product_pk>/digital/<int:item_pk>/delete/",
        ProductDeleteDigitalView.as_view(),
        name="product_delete_digital",
    ),
    path(
        "products/<int:product_pk>/media/<int:media_pk>/delete/",
        ProductDeleteMediaView.as_view(),
        name="product_delete_media",
    ),
    path("categories/", CategoriesView.as_view(), name="categories"),
    path("categories/new/", CategoryEditView.as_view(), name="category_new"),
    path("categories/<int:pk>/", CategoryEditView.as_view(), name="category_edit"),
    path("users/", UsersView.as_view(), name="users"),
    path("users/<int:pk>/", UserEditView.as_view(), name="user_edit"),
    path("orders/", OrdersView.as_view(), name="orders"),
    path("orders/export/", OrdersExportView.as_view(), name="orders_export"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
    path("orders/<int:pk>/edit/", OrderEditView.as_view(), name="order_edit"),
    path("reviews/", ReviewsView.as_view(), name="reviews"),
    path("reviews/moderate/", ReviewModerateView.as_view(), name="review_moderate"),
    path("settings/", SettingsView.as_view(), name="settings"),
    path("security/", SecurityLogView.as_view(), name="security_log"),
    path("support/", SupportTicketsView.as_view(), name="support_list"),
    path("support/<int:pk>/", SupportTicketDetailView.as_view(), name="support_detail"),
]

