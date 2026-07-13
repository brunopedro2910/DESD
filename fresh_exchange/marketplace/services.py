from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Sum

from django.utils import timezone

from .models import Cart, CartItem, Notification, Order, OrderLine, PaymentTransaction, Product, Settlement, SupplierOrder, SupplierOrderEvent


@transaction.atomic
def add_product_to_cart(user, product, quantity):
    if not product.purchasable:
        raise ValidationError("This product is not currently available.")
    if quantity < 1 or quantity > product.stock:
        raise ValidationError("The requested quantity is not available.")
    cart, _ = Cart.objects.get_or_create(user=user)
    item, created = CartItem.objects.select_for_update().get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity},
    )
    if not created:
        new_quantity = item.quantity + quantity
        if new_quantity > product.stock:
            raise ValidationError("The basket quantity is higher than the available stock.")
        item.quantity = new_quantity
        item.save(update_fields=["quantity"])
    return item


@transaction.atomic
def checkout_cart(user, address, instructions="", delivery_dates=None):
    cart = Cart.objects.select_for_update().get(user=user)
    items = list(cart.items.select_related("product__producer"))
    if not items:
        raise ValidationError("Your basket is empty.")

    total = Decimal("0")
    locked_products = {}
    for item in items:
        product = Product.objects.select_for_update().select_related("producer").get(pk=item.product_id)
        if not product.purchasable or item.quantity > product.stock:
            raise ValidationError(f"{product.name} no longer has enough stock.")
        locked_products[item.product_id] = product
        total += product.active_price * item.quantity

    order = Order.objects.create(
        customer=user,
        address=address,
        total=total,
        special_instructions=instructions,
        is_bulk=user.role == user.Role.COMMUNITY,
    )

    grouped_items = {}
    for item in items:
        grouped_items.setdefault(locked_products[item.product_id].producer, []).append(item)

    delivery_dates = delivery_dates or {}
    supplier_orders = {}
    for producer, producer_items in grouped_items.items():
        earliest = timezone.localdate() + timedelta(days=max(2, (producer.lead_time_hours + 23) // 24))
        requested = delivery_dates.get(producer.pk, earliest)
        if requested < earliest:
            raise ValidationError(f"{producer.name} needs at least {producer.lead_time_hours} hours to prepare an order.")
        gross = sum((locked_products[item.product_id].active_price * item.quantity for item in producer_items), Decimal("0"))
        commission, payout = settlement_values(gross)
        supplier_orders[producer.pk] = SupplierOrder.objects.create(
            order=order, producer=producer, delivery_date=requested,
            gross=gross, commission=commission, producer_payout=payout,
        )
        SupplierOrderEvent.objects.create(
            supplier_order=supplier_orders[producer.pk], status=SupplierOrder.Status.PENDING, changed_by=user,
        )

    for item in items:
        product = locked_products[item.product_id]
        OrderLine.objects.create(
            order=order,
            producer=product.producer,
            product_name=product.name,
            quantity=item.quantity,
            unit_price=product.active_price,
            supplier_order=supplier_orders[product.producer_id],
        )
        Product.objects.filter(pk=product.pk).update(stock=F("stock") - item.quantity)
        remaining_stock = product.stock - item.quantity
        if remaining_stock <= product.low_stock_level:
            Notification.objects.create(
                user=product.producer.user,
                title="Low stock",
                message=f"{product.name} has {remaining_stock} {product.unit} remaining.",
            )
        Notification.objects.create(
            user=product.producer.user,
            title="New local order",
            message=f"{item.quantity} x {product.name} is included in order {order.pk}.",
        )
    cart.items.all().delete()
    PaymentTransaction.objects.create(
        order=order, reference=f"TEST-{uuid4().hex[:12].upper()}", amount=total,
    )
    Notification.objects.create(user=user, title="Order confirmed", message=f"Order {order.pk} has been created successfully.")
    return order


def settlement_values(gross):
    commission = (gross * Decimal("0.05")).quantize(Decimal("0.01"))
    return commission, gross - commission


def generate_weekly_settlements(period_end=None):
    period_end = period_end or timezone.localdate()
    period_start = period_end - timedelta(days=6)
    totals = (
        SupplierOrder.objects.filter(
            status=SupplierOrder.Status.DELIVERED,
            updated_at__date__range=(period_start, period_end),
        )
        .values("producer")
        .annotate(gross_total=Sum("gross"), commission_total=Sum("commission"), payout_total=Sum("producer_payout"))
    )
    settlements = []
    for total in totals:
        settlement, _ = Settlement.objects.update_or_create(
            producer_id=total["producer"],
            period_start=period_start,
            period_end=period_end,
            defaults={
                "gross": total["gross_total"],
                "commission": total["commission_total"],
                "net": total["payout_total"],
            },
        )
        settlements.append(settlement)
    return settlements
