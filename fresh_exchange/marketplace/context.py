from .models import Cart


def market_context(request):
    basket_count = 0
    unread_count = 0
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        basket_count = sum(cart.items.values_list("quantity", flat=True))
        unread_count = request.user.notifications.filter(read=False).count()
    return {"basket_count": basket_count, "unread_count": unread_count}
