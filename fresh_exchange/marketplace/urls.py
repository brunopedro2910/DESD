from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api, views


router = DefaultRouter()
router.register("categories", api.CategoryViewSet, basename="api-category")
router.register("products", api.ProductViewSet, basename="api-product")
router.register("orders", api.OrderViewSet, basename="api-order")

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.SecureLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("market/", views.ProductList.as_view(), name="products"),
    path("market/<slug:slug>/", views.product_detail, name="product"),
    path("basket/", views.cart, name="cart"),
    path("basket/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("basket/remove/<int:item_id>/", views.remove_cart_item, name="remove_cart_item"),
    path("basket/update/<int:item_id>/", views.update_cart_item, name="update_cart_item"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/<int:order_id>/success/", views.order_success, name="order_success"),
    path("account/", views.dashboard, name="dashboard"),
    path("account/orders/", views.order_history, name="orders"),
    path("account/orders/<int:order_id>/receipt/", views.order_receipt, name="order_receipt"),
    path("account/orders/<int:order_id>/reorder/", views.reorder, name="reorder"),
    path("account/addresses/", views.addresses, name="addresses"),
    path("products/<int:product_id>/review/", views.add_review, name="add_review"),
    path("producer/", views.producer_dashboard, name="producer_dashboard"),
    path("producer/orders/", views.producer_orders, name="producer_orders"),
    path("producer/orders/<int:supplier_order_id>/status/", views.update_supplier_order, name="update_supplier_order"),
    path("producer/products/new/", views.product_form, name="product_new"),
    path("producer/products/<int:product_id>/edit/", views.product_form, name="product_edit"),
    path("producer/products/<int:product_id>/rescue/", views.surplus_form, name="surplus_form"),
    path("producer/content/", views.content_hub, name="content_hub"),
    path("producer/content/story/", views.story_form, name="story_new"),
    path("producer/content/recipe/", views.recipe_form, name="recipe_new"),
    path("producer/settlements/", views.settlements, name="settlements"),
    path("stories/", views.stories, name="stories"),
    path("surplus/", views.surplus, name="surplus"),
    path("recurring/", views.recurring, name="recurring"),
    path("recurring/<int:recurring_id>/action/", views.recurring_action, name="recurring_action"),
    path("notifications/", views.notifications, name="notifications"),
    path("network/financial-report/", views.financial_report, name="financial_report"),
    path("api/health/", api.health, name="api-health"),
    path("api/", include(router.urls)),
]
