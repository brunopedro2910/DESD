from hashlib import sha256

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
from django.views.generic import CreateView, ListView

from .forms import AddressForm, ProductForm, RecipeForm, RecurringOrderForm, RegistrationForm, ReviewForm, StoryForm, SurplusDealForm
from .models import Address, Cart, Category, LoginAudit, Order, Producer, Product, Recipe, RecurringOrder, Review, Settlement, Story, SupplierOrder, SupplierOrderEvent, SurplusDeal, User
from .services import add_product_to_cart, checkout_cart


class SecureLoginView(LoginView):
    template_name = "marketplace/login.html"
    attempt_limit = 5
    lock_seconds = 15 * 60

    def attempt_key(self):
        username = self.request.POST.get("username", "").strip().lower()
        ip_address = self.request.META.get("REMOTE_ADDR", "unknown")
        digest = sha256(f"{ip_address}:{username}".encode()).hexdigest()
        return f"login-attempts:{digest}"

    def post(self, request, *args, **kwargs):
        key = self.attempt_key()
        if cache.get(key, 0) >= self.attempt_limit:
            form = self.get_form()
            form.add_error(None, "Too many unsuccessful attempts. Try again in 15 minutes.")
            return self.form_invalid(form)

        response = super().post(request, *args, **kwargs)
        successful = request.user.is_authenticated
        LoginAudit.objects.create(
            username=request.POST.get("username", "")[:150],
            ip_address=request.META.get("REMOTE_ADDR") or None,
            successful=successful,
        )
        if successful:
            cache.delete(key)
            request.session.set_expiry(14 * 24 * 60 * 60 if request.POST.get("remember_me") else 0)
        else:
            current = cache.get(key, 0)
            cache.set(key, current + 1, self.lock_seconds)
        return response


def home(request):
    products = Product.objects.select_related("producer", "category").filter(availability=Product.Availability.AVAILABLE, stock__gt=0)[:6]
    return render(request, "marketplace/home.html", {"products": products})


def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("dashboard")
    return render(request, "marketplace/register.html", {"form": form})


class ProductList(ListView):
    template_name = "marketplace/products.html"
    context_object_name = "products"
    paginate_by = 18

    def get_queryset(self):
        queryset = Product.objects.select_related("producer", "category").prefetch_related("allergens").filter(availability=Product.Availability.AVAILABLE, stock__gt=0)
        query = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "")
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(producer__name__icontains=query))
        if category:
            queryset = queryset.filter(category__slug=category)
        if self.request.GET.get("organic") == "true":
            queryset = queryset.filter(organic=True)
        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all().order_by("name")
        context["query"] = self.request.GET.get("q", "")
        context["active_category"] = self.request.GET.get("category", "")
        context["organic_only"] = self.request.GET.get("organic") == "true"
        return context


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("producer", "category").prefetch_related("allergens", "reviews__customer"), slug=slug)
    review_form = ReviewForm()
    reviews = product.reviews.select_related("customer")
    rating_values = list(reviews.values_list("rating", flat=True))
    rating_average = round(sum(rating_values) / len(rating_values), 1) if rating_values else None
    return render(request, "marketplace/product.html", {"product": product, "review_form": review_form, "reviews": reviews, "rating_average": rating_average, "related_recipes": product.recipes.filter(published=True).select_related("producer")})


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    try:
        add_product_to_cart(request.user, product, int(request.POST.get("quantity", 1)))
        messages.success(request, f"{product.name} was added to your basket.")
    except (ValidationError, ValueError) as error:
        messages.error(request, str(error))
    return redirect(request.POST.get("next") or "cart")


@login_required
def cart(request):
    active_cart, _ = Cart.objects.get_or_create(user=request.user)
    items = active_cart.items.select_related("product__producer")
    return render(request, "marketplace/cart.html", {"items": items})


@login_required
@require_POST
def remove_cart_item(request, item_id):
    request.user.cart.items.filter(pk=item_id).delete()
    return redirect("cart")


@login_required
@require_POST
def update_cart_item(request, item_id):
    item = get_object_or_404(request.user.cart.items.select_related("product"), pk=item_id)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except ValueError:
        quantity = 0
    if quantity < 1:
        item.delete()
    elif quantity <= item.product.stock:
        item.quantity = quantity
        item.save(update_fields=["quantity"])
    else:
        messages.error(request, f"Only {item.product.stock} {item.product.unit} are available.")
    return redirect("cart")


@login_required
def checkout(request):
    addresses = request.user.addresses.all()
    active_cart, _ = Cart.objects.get_or_create(user=request.user)
    items = active_cart.items.select_related("product__producer")
    producers = {item.product.producer for item in items}
    if request.method == "POST":
        address = get_object_or_404(addresses, pk=request.POST.get("address"))
        try:
            delivery_dates = {producer.pk: parse_date(request.POST.get(f"delivery_{producer.pk}", "")) for producer in producers}
            delivery_dates = {key: value for key, value in delivery_dates.items() if value}
            order = checkout_cart(request.user, address, request.POST.get("instructions", ""), delivery_dates)
            return redirect("order_success", order_id=order.pk)
        except ValidationError as error:
            messages.error(request, str(error))
    return render(request, "marketplace/checkout.html", {"addresses": addresses, "items": items, "producers": producers})


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, customer=request.user)
    return render(request, "marketplace/order_success.html", {"order": order})


@login_required
def dashboard(request):
    if request.user.role == User.Role.PRODUCER and hasattr(request.user, "producer"):
        return redirect("producer_dashboard")
    return render(request, "marketplace/dashboard.html", {"orders": request.user.orders.order_by("-created_at")[:5]})


@login_required
def order_history(request):
    return render(request, "marketplace/orders.html", {"orders": request.user.orders.prefetch_related("lines").order_by("-created_at")})


@login_required
def order_receipt(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("lines"), pk=order_id, customer=request.user)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="gather-order-{order.pk}.csv"'
    response.write("product,producer,quantity,unit_price\n")
    for line in order.lines.all():
        response.write(f'"{line.product_name}","{line.producer.name}",{line.quantity},{line.unit_price}\n')
    return response


@login_required
@require_POST
def reorder(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("lines"), pk=order_id, customer=request.user)
    added = 0
    for line in order.lines.all():
        product = Product.objects.filter(producer=line.producer, name=line.product_name).first()
        if product and product.purchasable:
            try:
                add_product_to_cart(request.user, product, min(line.quantity, product.stock))
                added += 1
            except ValidationError:
                pass
    messages.success(request, f"{added} available product(s) were returned to my basket.")
    return redirect("cart")


@login_required
def addresses(request):
    form = AddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        if address.is_default:
            request.user.addresses.update(is_default=False)
        address.save()
        return redirect("addresses")
    return render(request, "marketplace/addresses.html", {"form": form, "addresses": request.user.addresses.all()})


@login_required
@require_POST
def add_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if not Order.objects.filter(customer=request.user, lines__product_name=product.name, status=Order.Status.COMPLETE).exists():
        return HttpResponseForbidden("Only verified customers can review this product.")
    form = ReviewForm(request.POST)
    if form.is_valid():
        Review.objects.update_or_create(product=product, customer=request.user, defaults=form.cleaned_data)
    return redirect("product", slug=product.slug)


@login_required
def producer_dashboard(request):
    if request.user.role != User.Role.PRODUCER or not hasattr(request.user, "producer"):
        return HttpResponseForbidden()
    producer = request.user.producer
    products = producer.products.order_by("name")
    supplier_orders = producer.supplier_orders.prefetch_related("lines").select_related("order__customer").order_by("delivery_date")
    gross = supplier_orders.aggregate(total=Sum("gross"))["total"] or 0
    return render(request, "marketplace/producer_dashboard.html", {"producer": producer, "products": products, "supplier_orders": supplier_orders[:12], "gross": gross})


@login_required
def producer_orders(request):
    producer = getattr(request.user, "producer", None)
    if not producer:
        return HttpResponseForbidden()
    orders = producer.supplier_orders.select_related("order__customer", "order__address").prefetch_related("lines").order_by("delivery_date")
    return render(request, "marketplace/producer_orders.html", {"producer": producer, "supplier_orders": orders})


@login_required
@require_POST
def update_supplier_order(request, supplier_order_id):
    producer = getattr(request.user, "producer", None)
    if not producer:
        return HttpResponseForbidden()
    supplier_order = get_object_or_404(SupplierOrder, pk=supplier_order_id, producer=producer)
    allowed_transitions = {
        SupplierOrder.Status.PENDING: {SupplierOrder.Status.CONFIRMED, SupplierOrder.Status.CANCELLED},
        SupplierOrder.Status.CONFIRMED: {SupplierOrder.Status.PREPARING, SupplierOrder.Status.CANCELLED},
        SupplierOrder.Status.PREPARING: {SupplierOrder.Status.READY},
        SupplierOrder.Status.READY: {SupplierOrder.Status.DELIVERED},
        SupplierOrder.Status.DELIVERED: set(),
        SupplierOrder.Status.CANCELLED: set(),
    }
    new_status = request.POST.get("status")
    if new_status in allowed_transitions[supplier_order.status]:
        supplier_order.status = new_status
        supplier_order.save(update_fields=["status", "updated_at"])
        SupplierOrderEvent.objects.create(supplier_order=supplier_order, status=new_status, changed_by=request.user, note=request.POST.get("note", "")[:240])
        supplier_order.order.customer.notifications.create(
            title="Order status updated",
            message=f"The {supplier_order.producer.name} part of order {supplier_order.order_id} is now {supplier_order.get_status_display().lower()}.",
        )
        messages.success(request, f"Order {supplier_order.order_id} is now {supplier_order.get_status_display().lower()}.")
    else:
        messages.error(request, "That status would skip a required preparation stage.")
    return redirect("producer_orders")


@login_required
def product_form(request, product_id=None):
    producer = getattr(request.user, "producer", None)
    if not producer:
        return HttpResponseForbidden()
    product = get_object_or_404(Product, pk=product_id, producer=producer) if product_id else None
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.producer = producer
        product.save()
        form.save_m2m()
        return redirect("producer_dashboard")
    return render(request, "marketplace/form.html", {"form": form, "title": "Edit product" if product else "Add product"})


@login_required
def surplus_form(request, product_id):
    producer = getattr(request.user, "producer", None)
    if not producer:
        return HttpResponseForbidden()
    product = get_object_or_404(Product, pk=product_id, producer=producer)
    deal = SurplusDeal.objects.filter(product=product).first()
    form = SurplusDealForm(request.POST or None, instance=deal)
    if request.method == "POST" and form.is_valid():
        deal = form.save(commit=False)
        deal.product = product
        deal.save()
        messages.success(request, f"The rescue offer for {product.name} is live.")
        return redirect("producer_dashboard")
    return render(request, "marketplace/form.html", {"form": form, "title": f"Rescue offer for {product.name}"})


@login_required
def content_hub(request):
    producer = getattr(request.user, "producer", None)
    if not producer:
        return HttpResponseForbidden()
    return render(request, "marketplace/content_hub.html", {"stories": producer.stories.all(), "recipes": producer.recipes.all()})


@login_required
def story_form(request):
    producer = getattr(request.user, "producer", None)
    if not producer:
        return HttpResponseForbidden()
    form = StoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        story = form.save(commit=False)
        story.producer = producer
        story.save()
        return redirect("content_hub")
    return render(request, "marketplace/form.html", {"form": form, "title": "Publish a farm story"})


@login_required
def recipe_form(request):
    producer = getattr(request.user, "producer", None)
    if not producer:
        return HttpResponseForbidden()
    form = RecipeForm(request.POST or None, producer=producer)
    if request.method == "POST" and form.is_valid():
        recipe = form.save(commit=False)
        recipe.producer = producer
        recipe.save()
        return redirect("content_hub")
    return render(request, "marketplace/form.html", {"form": form, "title": "Add a local recipe"})


def stories(request):
    return render(request, "marketplace/stories.html", {"stories": Story.objects.filter(published=True).select_related("producer"), "recipes": Recipe.objects.filter(published=True).select_related("producer")})


def surplus(request):
    deals = SurplusDeal.objects.select_related("product__producer").order_by("expires_at")
    return render(request, "marketplace/surplus.html", {"deals": [deal for deal in deals if deal.active]})


@login_required
def recurring(request):
    if request.user.role != User.Role.RESTAURANT:
        return HttpResponseForbidden()
    form = RecurringOrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.restaurant = request.user
        item.save()
        return redirect("recurring")
    return render(request, "marketplace/recurring.html", {"form": form, "items": request.user.recurring_orders.select_related("product")})


@login_required
@require_POST
def recurring_action(request, recurring_id):
    if request.user.role != User.Role.RESTAURANT:
        return HttpResponseForbidden()
    item = get_object_or_404(RecurringOrder, pk=recurring_id, restaurant=request.user)
    action = request.POST.get("action")
    if action == "toggle":
        item.active = not item.active
        item.save(update_fields=["active"])
    elif action == "delete":
        item.delete()
    return redirect("recurring")


@login_required
def settlements(request):
    producer = getattr(request.user, "producer", None)
    if not producer:
        return HttpResponseForbidden()
    return render(request, "marketplace/settlements.html", {"settlements": producer.settlements.order_by("-period_end")})


@login_required
def notifications(request):
    request.user.notifications.update(read=True)
    return render(request, "marketplace/notifications.html", {"notifications": request.user.notifications.order_by("-created_at")})


@login_required
def financial_report(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    supplier_orders = SupplierOrder.objects.select_related("producer", "order").order_by("-order__created_at")
    date_from = parse_date(request.GET.get("date_from", ""))
    date_to = parse_date(request.GET.get("date_to", ""))
    producer_id = request.GET.get("producer", "")
    if date_from:
        supplier_orders = supplier_orders.filter(order__created_at__date__gte=date_from)
    if date_to:
        supplier_orders = supplier_orders.filter(order__created_at__date__lte=date_to)
    if producer_id:
        supplier_orders = supplier_orders.filter(producer_id=producer_id)
    totals = supplier_orders.aggregate(gross=Sum("gross"), commission=Sum("commission"), payouts=Sum("producer_payout"))
    if request.GET.get("format") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="gather-financial-report.csv"'
        response.write("order,producer,order_date,delivery_date,gross,commission,producer_payout,status\n")
        for supplier_order in supplier_orders:
            response.write(
                f'{supplier_order.order_id},"{supplier_order.producer.name}",{supplier_order.order.created_at.date()},'
                f'{supplier_order.delivery_date},{supplier_order.gross},{supplier_order.commission},'
                f'{supplier_order.producer_payout},{supplier_order.status}\n'
            )
        return response
    return render(request, "marketplace/financial_report.html", {
        "supplier_orders": supplier_orders,
        "totals": totals,
        "producers": Producer.objects.order_by("name"),
        "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""),
        "selected_producer": producer_id,
    })
