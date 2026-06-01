from rest_framework import serializers

from apps.catalog.models import Product
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "price", "quantity"]
        read_only_fields = ["id", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "amount",
            "currency",
            "transaction_id",
            "created_at",
            "items",
        ]
        read_only_fields = ["id", "status", "transaction_id", "created_at"]

    def create(self, validated_data):
        request = self.context["request"]
        items_data = validated_data.pop("items", [])
        amount = 0
        order = Order.objects.create(
            user=request.user,
            amount=0,
            currency=validated_data.get("currency", "RUB"),
        )
        for item in items_data:
            product = Product.objects.get(pk=item["product"].id)
            qty = item.get("quantity", 1)
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=qty,
            )
            amount += product.price * qty
        order.amount = amount
        order.save(update_fields=["amount"])
        return order

