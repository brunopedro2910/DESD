from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        PRODUCER = "producer", "Producer"
        COMMUNITY = "community", "Community group"
        RESTAURANT = "restaurant", "Restaurant"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=30, blank=True)


class Producer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="producer")
    name = models.CharField(max_length=120)
    story = models.TextField(blank=True)
    postcode = models.CharField(max_length=12)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    verified = models.BooleanField(default=False)
    lead_time_hours = models.PositiveSmallIntegerField(default=48)
    contact_name = models.CharField(max_length=120, blank=True)
    address = models.CharField(max_length=180, blank=True)

    def __str__(self):
        return self.name

    @property
    def food_miles(self):
        if self.latitude is None or self.longitude is None:
            return None
        bristol_lat, bristol_lon = radians(51.4545), radians(-2.5879)
        producer_lat, producer_lon = radians(float(self.latitude)), radians(float(self.longitude))
        delta_lat = producer_lat - bristol_lat
        delta_lon = producer_lon - bristol_lon
        arc = 2 * asin(sqrt(sin(delta_lat / 2) ** 2 + cos(bristol_lat) * cos(producer_lat) * sin(delta_lon / 2) ** 2))
        return round(3958.8 * arc, 1)


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=50, default="Home")
    line_1 = models.CharField(max_length=150)
    city = models.CharField(max_length=80, default="Bristol")
    postcode = models.CharField(max_length=12)
    is_default = models.BooleanField(default=False)


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Allergen(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    class Availability(models.TextChoices):
        AVAILABLE = "available", "Available"
        PAUSED = "paused", "Paused"
        SOLD_OUT = "sold_out", "Sold out"

    producer = models.ForeignKey(Producer, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=30, default="item")
    stock = models.PositiveIntegerField(default=0)
    low_stock_level = models.PositiveIntegerField(default=5)
    availability = models.CharField(max_length=16, choices=Availability.choices, default=Availability.AVAILABLE)
    organic = models.BooleanField(default=False)
    season_start = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(12)])
    season_end = models.PositiveSmallIntegerField(default=12, validators=[MinValueValidator(1), MaxValueValidator(12)])
    allergens = models.ManyToManyField(Allergen, blank=True)
    image = models.ImageField(upload_to="products/", blank=True)
    harvest_date = models.DateField(null=True, blank=True)
    best_before_date = models.DateField(null=True, blank=True)
    allergen_notes = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def in_season(self):
        month = timezone.localdate().month
        if self.season_start <= self.season_end:
            return self.season_start <= month <= self.season_end
        return month >= self.season_start or month <= self.season_end

    @property
    def active_price(self):
        deal = getattr(self, "surplus", None)
        return deal.discounted_price if deal and deal.active else self.price

    @property
    def purchasable(self):
        return self.availability == self.Availability.AVAILABLE and self.stock > 0

    def __str__(self):
        return self.name


class SurplusDeal(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="surplus")
    discount = models.PositiveSmallIntegerField(validators=[MinValueValidator(10), MaxValueValidator(50)])
    expires_at = models.DateTimeField()

    @property
    def active(self):
        return self.expires_at > timezone.now()

    @property
    def discounted_price(self):
        return (self.product.price * (Decimal("100") - self.discount) / Decimal("100")).quantize(Decimal("0.01"))


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")

    @property
    def total(self):
        return sum((item.subtotal for item in self.items.select_related("product")), Decimal("0"))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["cart", "product"], name="one_product_per_cart")]

    @property
    def subtotal(self):
        return self.product.active_price * self.quantity


class Order(models.Model):
    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        COMPLETE = "complete", "Complete"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PAID)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = models.TextField(blank=True)
    is_bulk = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class SupplierOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="supplier_orders")
    producer = models.ForeignKey(Producer, on_delete=models.PROTECT, related_name="supplier_orders")
    delivery_date = models.DateField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    gross = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    producer_payout = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "producer"], name="one_supplier_order_per_producer")]


class SupplierOrderEvent(models.Model):
    supplier_order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=16, choices=SupplierOrder.Status.choices)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    producer = models.ForeignKey(Producer, on_delete=models.PROTECT, related_name="order_lines")
    product_name = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    supplier_order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE, related_name="lines", null=True)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class RecurringOrder(models.Model):
    restaurant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recurring_orders")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    weekday = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(6)])
    next_run = models.DateField()
    active = models.BooleanField(default=True)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    producer_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["product", "customer"], name="one_review_per_product")]


class Story(models.Model):
    producer = models.ForeignKey(Producer, on_delete=models.CASCADE, related_name="stories")
    title = models.CharField(max_length=150)
    body = models.TextField()
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Recipe(models.Model):
    producer = models.ForeignKey(Producer, on_delete=models.CASCADE, related_name="recipes")
    title = models.CharField(max_length=150)
    ingredients = models.TextField()
    method = models.TextField()
    products = models.ManyToManyField(Product, related_name="recipes", blank=True)
    published = models.BooleanField(default=True)


class Settlement(models.Model):
    producer = models.ForeignKey(Producer, on_delete=models.CASCADE, related_name="settlements")
    period_start = models.DateField()
    period_end = models.DateField()
    gross = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    net = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["producer", "period_start", "period_end"], name="one_settlement_per_producer_period")]


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=120)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class PaymentTransaction(models.Model):
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="payment")
    reference = models.CharField(max_length=40, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    provider = models.CharField(max_length=30, default="Assessment test gateway")
    status = models.CharField(max_length=20, default="accepted")
    created_at = models.DateTimeField(auto_now_add=True)


class LoginAudit(models.Model):
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    successful = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
