from rest_framework import serializers

from .models import Category, Product, ProductMedia, Review


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "sort_order"]


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ["id", "media_type", "url", "sort_order"]


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "user_email", "rating", "text", "created_at"]
        read_only_fields = ["id", "user_email", "created_at"]

    def get_user_email(self, obj):
        return obj.user.email if obj.user else "Аноним"


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    media = ProductMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "description",
            "price",
            "product_type",
            "license_type",
            "purpose",
            "status",
            "created_at",
            "category",
            "media",
        ]

