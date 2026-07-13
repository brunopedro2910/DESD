from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, Allergen, Cart, CartItem, Category, LoginAudit, Notification, Order, OrderLine, Producer, Product, Recipe, RecurringOrder, Review, Settlement, Story, SurplusDeal, User


admin.site.register(User, UserAdmin)
admin.site.register([Address, Allergen, Cart, CartItem, Category, LoginAudit, Notification, Order, OrderLine, Producer, Product, Recipe, RecurringOrder, Review, Settlement, Story, SurplusDeal])
