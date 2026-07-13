from rest_framework import serializers

from .models import Category, Order, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class ProductSerializer(serializers.ModelSerializer):
    producer_name = serializers.CharField(source="producer.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    active_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "slug", "description", "price", "active_price", "unit", "stock", "organic", "availability", "producer", "producer_name", "category", "category_name")
        read_only_fields = ("producer",)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "status", "total", "is_bulk", "created_at")
