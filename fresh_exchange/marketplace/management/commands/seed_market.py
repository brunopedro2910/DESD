from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from marketplace.models import Address, Category, Producer, Product, Recipe, Settlement, Story, SurplusDeal, User


class Command(BaseCommand):
    help = "Create deterministic Gather demonstration data."

    def handle(self, *args, **options):
        category_names = [
            ("Vegetables", "vegetables"), ("Fruit", "fruit"), ("Bakery", "bakery"),
            ("Pantry", "pantry"), ("Dairy", "dairy"), ("Eggs", "eggs"),
            ("Drinks", "drinks"), ("Seasonal", "seasonal"),
        ]
        categories = {slug: Category.objects.get_or_create(name=name, slug=slug)[0] for name, slug in category_names}

        producer_data = {
            "north": ("gather_producer", "Maya", "North Street Growers", "BS3 1JP", "51.4420", "-2.6008", "A small Bristol market garden focused on seasonal produce."),
            "harbour": ("harbour_dairy", "Elena", "Harbour Dairy", "BS20 7XJ", "51.4848", "-2.7674", "Cultured dairy and eggs supplied by a family farm west of Bristol."),
            "easton": ("easton_bakehouse", "Sam", "Easton Bakehouse", "BS5 6XX", "51.4625", "-2.5510", "Slow bread, pastries and pantry staples made in Easton."),
            "orchard": ("orchard_and_jar", "Nia", "Orchard & Jar", "BS40 5TP", "51.3442", "-2.6872", "Fruit, juice and preserves made from small Somerset orchards."),
        }
        producers = {}
        for key, (username, first_name, name, postcode, latitude, longitude, story) in producer_data.items():
            user, _ = User.objects.get_or_create(username=username, defaults={"first_name": first_name, "role": User.Role.PRODUCER})
            user.first_name = first_name
            user.role = User.Role.PRODUCER
            user.set_password("GatherDemo!2026")
            user.save()
            profile, _ = Producer.objects.get_or_create(user=user, defaults={"name": name, "postcode": postcode, "verified": True, "story": story})
            profile.name, profile.postcode, profile.story = name, postcode, story
            profile.latitude, profile.longitude = Decimal(latitude), Decimal(longitude)
            profile.verified, profile.lead_time_hours = True, 48
            profile.save()
            producers[key] = profile

        customer, _ = User.objects.get_or_create(username="gather_customer", defaults={"first_name": "Local", "role": User.Role.CUSTOMER})
        customer.set_password("GatherDemo!2026")
        customer.save()
        Address.objects.get_or_create(user=customer, label="Home", defaults={"line_1": "24 Demo Street", "city": "Bristol", "postcode": "BS1 4ST", "is_default": True})

        restaurant, _ = User.objects.get_or_create(username="gather_restaurant", defaults={"first_name": "Harbour Kitchen", "role": User.Role.RESTAURANT})
        restaurant.set_password("GatherDemo!2026")
        restaurant.save()

        admin, _ = User.objects.get_or_create(username="gather_admin", defaults={"first_name": "Bruno", "is_staff": True, "is_superuser": True})
        admin.is_staff = admin.is_superuser = True
        admin.set_password("GatherDemo!2026")
        admin.save()

        # I keep this list explicit so my demo data stays predictable on every machine.
        products = [
            ("Rainbow Tomatoes", "fruit", "north", "Mixed heritage tomatoes picked at full colour.", "4.80", "punnet", True),
            ("Garden Peas", "vegetables", "north", "Sweet podded peas grown within Bristol.", "3.20", "bag", True),
            ("Purple Carrots", "vegetables", "north", "Earthy seasonal carrots sold with their tops.", "2.90", "bunch", True),
            ("Tenderstem Broccoli", "vegetables", "north", "Fresh green stems with a delicate crunch.", "3.40", "bunch", False),
            ("New Potatoes", "vegetables", "north", "Waxy early potatoes lifted from rich soil.", "3.60", "1kg", True),
            ("Summer Courgettes", "vegetables", "north", "Small courgettes selected for sweetness.", "2.70", "pair", True),
            ("Rainbow Chard", "vegetables", "north", "Colourful leaves and crisp stems for quick cooking.", "2.85", "bunch", False),
            ("Little Gem Lettuce", "vegetables", "north", "Two compact heads with crisp inner leaves.", "2.30", "pair", True),
            ("English Strawberries", "fruit", "orchard", "Fragrant berries gathered in the cool morning.", "4.95", "punnet", False),
            ("Ripe Gooseberries", "fruit", "orchard", "Sharp green fruit for puddings and compotes.", "3.75", "punnet", True),
            ("Somerset Cherries", "fruit", "orchard", "Dark sweet cherries from a small orchard block.", "5.40", "bag", False),
            ("Early Plums", "fruit", "orchard", "Soft aromatic plums with a gentle sharp edge.", "4.20", "punnet", False),
            ("Blackcurrants", "fruit", "orchard", "Deeply flavoured berries ready for baking.", "3.95", "punnet", True),
            ("Seeded Sourdough", "bakery", "easton", "Slow-fermented loaf with sunflower and pumpkin seeds.", "5.50", "loaf", False),
            ("Country White Loaf", "bakery", "easton", "Open crumb sourdough with a crisp floury crust.", "4.80", "loaf", False),
            ("Rye and Caraway", "bakery", "easton", "Dense rye loaf scented with toasted caraway.", "5.20", "loaf", False),
            ("Morning Buns", "bakery", "easton", "Laminated buns rolled with orange and cardamom.", "6.60", "box of 4", False),
            ("Oat and Honey Granola", "bakery", "easton", "Toasted oats, seeds and local wildflower honey.", "6.90", "bag", False),
            ("Strawberry Preserve", "pantry", "orchard", "Small-batch preserve made from surplus summer fruit.", "6.25", "jar", False),
            ("Gooseberry Jam", "pantry", "orchard", "Bright preserve with a clean citrus finish.", "5.90", "jar", False),
            ("Spiced Plum Chutney", "pantry", "orchard", "Rich orchard fruit simmered with warm spices.", "6.40", "jar", False),
            ("Wildflower Honey", "pantry", "easton", "Raw Bristol honey with a floral summer flavour.", "8.50", "jar", False),
            ("Rosemary Sea Salt", "pantry", "easton", "Flaky salt blended with locally grown rosemary.", "4.10", "pot", True),
            ("Apple Cider Vinegar", "pantry", "orchard", "Naturally fermented vinegar from pressed apples.", "5.75", "bottle", True),
            ("Fresh Curd", "dairy", "harbour", "Soft cultured curd for toast, salads and cooking.", "4.40", "pot", False),
            ("Whole Milk", "dairy", "harbour", "Creamy pasteurised milk bottled near the farm.", "2.20", "litre", False),
            ("Salted Farm Butter", "dairy", "harbour", "Slow-churned butter finished with sea salt.", "4.75", "block", False),
            ("Natural Yoghurt", "dairy", "harbour", "Thick live yoghurt with a gentle tang.", "3.60", "pot", False),
            ("Mature Farmhouse Cheddar", "dairy", "harbour", "Clothbound cheddar with a rounded savoury finish.", "6.80", "wedge", False),
            ("Free Range Eggs", "eggs", "harbour", "Mixed-size eggs collected daily from outdoor hens.", "3.90", "half dozen", False),
            ("Large Free Range Eggs", "eggs", "harbour", "Six large eggs with rich golden yolks.", "4.40", "half dozen", False),
            ("Baker's Egg Tray", "eggs", "harbour", "A larger tray suited to baking and hospitality.", "8.90", "tray of 15", False),
            ("Quail Eggs", "eggs", "harbour", "Delicate speckled eggs from a small local flock.", "4.95", "box of 12", False),
            ("Cloudy Apple Juice", "drinks", "orchard", "Pressed orchard apples with nothing added.", "4.60", "bottle", False),
            ("Blackcurrant Cordial", "drinks", "orchard", "A bold fruit cordial for water or sparkling drinks.", "6.20", "bottle", False),
            ("Rhubarb Shrub", "drinks", "orchard", "Sweet-sharp drinking vinegar made in small batches.", "7.10", "bottle", False),
            ("Sparkling Perry", "drinks", "orchard", "Lightly sparkling drink from traditional pears.", "8.75", "bottle", False),
            ("Courgette Flower Box", "seasonal", "north", "Fresh edible flowers packed carefully for cooking.", "7.50", "box", True),
            ("Summer Salad Crate", "seasonal", "north", "A changing mix of leaves, herbs and edible flowers.", "12.50", "crate", True),
            ("Picnic Produce Box", "seasonal", "north", "Crunchy vegetables and fruit selected for sharing.", "18.00", "box", False),
            ("Orchard Tasting Box", "seasonal", "orchard", "The week's best fruit chosen across several varieties.", "16.50", "box", False),
        ]

        product_by_slug = {}
        for name, category, producer_key, description, price, unit, organic in products:
            slug = name.lower().replace("'", "").replace(" ", "-")
            product, _ = Product.objects.get_or_create(
                slug=slug,
                defaults={"producer": producers[producer_key], "category": categories[category], "name": name,
                          "description": description, "price": Decimal(price), "unit": unit, "stock": 30,
                          "organic": organic},
            )
            product_by_slug[slug] = product

        SurplusDeal.objects.get_or_create(product=product_by_slug["strawberry-preserve"], defaults={"discount": 25, "expires_at": timezone.now() + timedelta(days=2)})
        Story.objects.get_or_create(producer=producers["north"], title="Why we leave the carrot tops on", defaults={"body": "The leaves show how recently the carrots were lifted, and they make a useful herb-like pesto.", "published": True})
        recipe, _ = Recipe.objects.get_or_create(producer=producers["north"], title="Tomato and fresh curd toast", defaults={"ingredients": "Sourdough\nRainbow tomatoes\nFresh curd\nHerbs", "method": "Toast the bread, spread the curd and finish with sliced tomatoes and herbs.", "published": True})
        recipe.products.add(product_by_slug["rainbow-tomatoes"], product_by_slug["fresh-curd"], product_by_slug["seeded-sourdough"])
        Settlement.objects.get_or_create(producer=producers["north"], period_start=timezone.localdate()-timedelta(days=7), period_end=timezone.localdate(), defaults={"gross": Decimal("200.00"), "commission": Decimal("10.00"), "net": Decimal("190.00")})
        self.stdout.write(self.style.SUCCESS(f"Gather demo data is ready with {len(products)} products."))
