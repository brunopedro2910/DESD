from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Address, Cart, Category, LoginAudit, Notification, PaymentTransaction, Producer, Product, RecurringOrder, Settlement, SupplierOrder, SupplierOrderEvent, SurplusDeal, User
from .services import add_product_to_cart, checkout_cart, generate_weekly_settlements, settlement_values


class MarketplaceTestCase(TestCase):
    def setUp(self):
        self.producer_user = User.objects.create_user("producer", password="A-secure-pass-123", role=User.Role.PRODUCER)
        self.producer = Producer.objects.create(user=self.producer_user, name="Test Farm", postcode="BS1")
        self.customer = User.objects.create_user("customer", password="A-secure-pass-123", role=User.Role.CUSTOMER)
        self.category = Category.objects.create(name="Vegetables", slug="vegetables")
        self.product = Product.objects.create(producer=self.producer, category=self.category, name="Carrots", slug="carrots", description="Fresh", price=Decimal("2.00"), stock=8, organic=True)
        self.address = Address.objects.create(user=self.customer, line_1="1 Test Road", postcode="BS1 1AA", is_default=True)

    def test_public_market_and_product_pages(self):
        self.assertEqual(self.client.get(reverse("products")).status_code, 200)
        self.assertEqual(self.client.get(reverse("product", args=[self.product.slug])).status_code, 200)

    def test_market_filters_search_and_organic(self):
        response = self.client.get(reverse("products"), {"q": "Carrot", "organic": "true"})
        self.assertContains(response, "Carrots")

    def test_add_to_cart_requires_valid_stock(self):
        item = add_product_to_cart(self.customer, self.product, 3)
        self.assertEqual(item.quantity, 3)
        with self.assertRaises(ValidationError):
            add_product_to_cart(self.customer, self.product, 9)

    def test_customer_can_update_basket_quantity(self):
        item = add_product_to_cart(self.customer, self.product, 2)
        self.client.force_login(self.customer)
        response = self.client.post(reverse("update_cart_item", args=[item.pk]), {"quantity": 4})
        item.refresh_from_db()
        self.assertRedirects(response, reverse("cart"))
        self.assertEqual(item.quantity, 4)

    def test_checkout_deducts_stock_and_splits_lines(self):
        add_product_to_cart(self.customer, self.product, 2)
        order = checkout_cart(self.customer, self.address)
        self.product.refresh_from_db()
        self.assertEqual(order.total, Decimal("4.00"))
        self.assertEqual(self.product.stock, 6)
        self.assertEqual(order.lines.get().producer, self.producer)
        supplier_order = order.supplier_orders.get()
        self.assertEqual(supplier_order.commission, Decimal("0.20"))
        self.assertEqual(supplier_order.producer_payout, Decimal("3.80"))
        self.assertEqual(PaymentTransaction.objects.get(order=order).status, "accepted")

    def test_multi_producer_checkout_creates_separate_supplier_orders(self):
        second_user = User.objects.create_user("producer-two", password="A-secure-pass-123", role=User.Role.PRODUCER)
        second_producer = Producer.objects.create(user=second_user, name="Second Farm", postcode="BS2")
        second_product = Product.objects.create(
            producer=second_producer, category=self.category, name="Kale", slug="kale", description="Fresh",
            price=Decimal("3.00"), stock=6,
        )
        add_product_to_cart(self.customer, self.product, 1)
        add_product_to_cart(self.customer, second_product, 2)
        order = checkout_cart(self.customer, self.address)
        self.assertEqual(order.supplier_orders.count(), 2)
        self.assertEqual(order.total, Decimal("8.00"))
        self.assertSetEqual(set(order.supplier_orders.values_list("producer_id", flat=True)), {self.producer.pk, second_producer.pk})

    def test_checkout_enforces_each_producers_lead_time(self):
        add_product_to_cart(self.customer, self.product, 1)
        too_early = timezone.localdate() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            checkout_cart(self.customer, self.address, delivery_dates={self.producer.pk: too_early})

    def test_checkout_creates_low_stock_notification(self):
        self.product.low_stock_level = 7
        self.product.save(update_fields=["low_stock_level"])
        add_product_to_cart(self.customer, self.product, 2)
        checkout_cart(self.customer, self.address)
        self.assertTrue(Notification.objects.filter(user=self.producer_user, title="Low stock").exists())

    def test_checkout_rejects_empty_cart(self):
        Cart.objects.create(user=self.customer)
        with self.assertRaises(ValidationError):
            checkout_cart(self.customer, self.address)

    def test_surplus_price_uses_discount(self):
        SurplusDeal.objects.create(product=self.product, discount=25, expires_at=timezone.now() + timedelta(days=1))
        self.assertEqual(self.product.active_price, Decimal("1.50"))

    def test_commission_is_five_percent(self):
        commission, net = settlement_values(Decimal("100.00"))
        self.assertEqual(commission, Decimal("5.00"))
        self.assertEqual(net, Decimal("95.00"))

    def test_api_health_and_products(self):
        self.assertEqual(self.client.get(reverse("api-health")).json()["status"], "ok")
        self.assertEqual(self.client.get("/api/products/").status_code, 200)

    def test_api_orders_are_scoped_to_authenticated_customer(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get("/api/orders/").status_code, 200)

    def test_producer_dashboard_blocks_customers(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("producer_dashboard")).status_code, 403)

    def test_supplier_status_endpoint_is_scoped_to_owner(self):
        add_product_to_cart(self.customer, self.product, 1)
        supplier_order = checkout_cart(self.customer, self.address).supplier_orders.get()
        other_user = User.objects.create_user("other-producer", password="A-secure-pass-123", role=User.Role.PRODUCER)
        Producer.objects.create(user=other_user, name="Other Farm", postcode="BS3")
        self.client.force_login(other_user)
        response = self.client.post(reverse("update_supplier_order", args=[supplier_order.pk]), {"status": SupplierOrder.Status.CONFIRMED})
        self.assertEqual(response.status_code, 404)

    def test_supplier_status_progression_creates_audit_event(self):
        add_product_to_cart(self.customer, self.product, 1)
        supplier_order = checkout_cart(self.customer, self.address).supplier_orders.get()
        self.client.force_login(self.producer_user)
        self.client.post(reverse("update_supplier_order", args=[supplier_order.pk]), {"status": SupplierOrder.Status.CONFIRMED})
        supplier_order.refresh_from_db()
        self.assertEqual(supplier_order.status, SupplierOrder.Status.CONFIRMED)
        self.assertTrue(SupplierOrderEvent.objects.filter(supplier_order=supplier_order, status=SupplierOrder.Status.CONFIRMED).exists())

    def test_financial_report_requires_staff(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("financial_report")).status_code, 403)
        admin = User.objects.create_user("admin", password="A-secure-pass-123", is_staff=True)
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("financial_report")).status_code, 200)

    def test_product_api_creation_assigns_producer(self):
        self.client.force_login(self.producer_user)
        response = self.client.post("/api/products/", {"name": "Beetroot", "slug": "beetroot", "description": "Fresh", "price": "3.00", "unit": "bunch", "stock": 5, "availability": "available", "category": self.category.pk}, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.objects.get(slug="beetroot").producer, self.producer)

    def test_password_is_hashed(self):
        self.assertNotEqual(self.customer.password, "A-secure-pass-123")
        self.assertTrue(self.customer.check_password("A-secure-pass-123"))

    def test_new_customer_can_open_empty_basket(self):
        new_customer = User.objects.create_user(username="new-customer", password="VerySecure123!", role=User.Role.CUSTOMER)
        self.client.force_login(new_customer)

        response = self.client.get(reverse("cart"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Cart.objects.filter(user=new_customer).exists())

    def test_customer_cannot_create_product_through_api(self):
        self.client.force_login(self.customer)
        response = self.client.post("/api/products/", {
            "name": "Customer product", "slug": "customer-product", "description": "Not allowed",
            "price": "2.50", "unit": "item", "stock": 2, "category": self.category.pk,
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Product.objects.filter(slug="customer-product").exists())

    def test_order_api_requires_authentication(self):
        response = self.client.get("/api/orders/")

        self.assertEqual(response.status_code, 403)

    def test_failed_login_is_audited(self):
        response = self.client.post(reverse("login"), {"username": "customer", "password": "wrong-password"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(LoginAudit.objects.filter(username="customer", successful=False).exists())

    def test_restaurant_can_pause_recurring_order(self):
        restaurant = User.objects.create_user("restaurant", password="A-secure-pass-123", role=User.Role.RESTAURANT)
        recurring = RecurringOrder.objects.create(restaurant=restaurant, product=self.product, quantity=2, next_run=timezone.localdate())
        self.client.force_login(restaurant)

        response = self.client.post(reverse("recurring_action", args=[recurring.pk]), {"action": "toggle"})

        recurring.refresh_from_db()
        self.assertRedirects(response, reverse("recurring"))
        self.assertFalse(recurring.active)

    def test_weekly_settlement_uses_delivered_supplier_orders(self):
        add_product_to_cart(self.customer, self.product, 2)
        supplier_order = checkout_cart(self.customer, self.address).supplier_orders.get()
        supplier_order.status = SupplierOrder.Status.DELIVERED
        supplier_order.save(update_fields=["status", "updated_at"])

        generated = generate_weekly_settlements()

        self.assertEqual(len(generated), 1)
        settlement = Settlement.objects.get(producer=self.producer)
        self.assertEqual(settlement.gross, Decimal("4.00"))
        self.assertEqual(settlement.commission, Decimal("0.20"))
        self.assertEqual(settlement.net, Decimal("3.80"))

    def test_staff_can_export_filtered_financial_csv(self):
        admin = User.objects.create_user("report-admin", password="A-secure-pass-123", is_staff=True)
        add_product_to_cart(self.customer, self.product, 1)
        checkout_cart(self.customer, self.address)
        self.client.force_login(admin)

        response = self.client.get(reverse("financial_report"), {"producer": self.producer.pk, "format": "csv"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("Test Farm", response.content.decode())
