from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import Address, Producer, Product, Recipe, RecurringOrder, Review, Story, SurplusDeal, User


class RegistrationForm(UserCreationForm):
    business_name = forms.CharField(max_length=120, required=False)
    address = forms.CharField(max_length=180)
    postcode = forms.CharField(max_length=12)
    accept_terms = forms.BooleanField()

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "role")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("role") == User.Role.PRODUCER and not cleaned.get("business_name"):
            self.add_error("business_name", "Enter the name customers will see for your business.")
        return cleaned

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=commit)
        if not commit:
            return user
        if user.role == User.Role.PRODUCER:
            Producer.objects.create(
                user=user,
                name=self.cleaned_data["business_name"],
                contact_name=f"{user.first_name} {user.last_name}".strip(),
                address=self.cleaned_data["address"],
                postcode=self.cleaned_data["postcode"],
            )
        else:
            Address.objects.create(
                user=user, label="Primary address", line_1=self.cleaned_data["address"],
                postcode=self.cleaned_data["postcode"], is_default=True,
            )
        return user


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ("producer", "created_at")
        widgets = {"description": forms.Textarea(attrs={"rows": 4}), "allergens": forms.CheckboxSelectMultiple()}


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ("user",)


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        exclude = ("producer", "created_at")


class RecipeForm(forms.ModelForm):
    def __init__(self, *args, producer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["products"].queryset = producer.products.order_by("name") if producer else Product.objects.none()

    class Meta:
        model = Recipe
        exclude = ("producer",)
        widgets = {"products": forms.CheckboxSelectMultiple()}


class RecurringOrderForm(forms.ModelForm):
    class Meta:
        model = RecurringOrder
        exclude = ("restaurant",)
        widgets = {"next_run": forms.DateInput(attrs={"type": "date"})}


class SurplusDealForm(forms.ModelForm):
    class Meta:
        model = SurplusDeal
        fields = ("discount", "expires_at")
        widgets = {"expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"})}
