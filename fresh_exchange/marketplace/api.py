from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Category, Order, Product
from .serializers import CategorySerializer, OrderSerializer, ProductSerializer


class IsProducerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and hasattr(request.user, "producer")


@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "service": "gather"})


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsProducerOrReadOnly]

    def get_queryset(self):
        queryset = Product.objects.select_related("producer", "category")
        query = self.request.query_params.get("search")
        if query:
            queryset = queryset.filter(name__icontains=query)
        if self.request.query_params.get("organic") == "true":
            queryset = queryset.filter(organic=True)
        return queryset.order_by("name")

    def perform_create(self, serializer):
        serializer.save(producer=self.request.user.producer)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by("-created_at")
