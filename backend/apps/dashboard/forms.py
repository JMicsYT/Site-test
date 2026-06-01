import re

from django import forms
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.catalog.models import Category, DigitalItem, Product, ProductMedia
from apps.core.models import SiteSetting
from apps.orders.models import Order

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SiteSettingsForm(forms.Form):
    payment_api_key = forms.CharField(
        label="Платёжный API ключ",
        required=False,
        widget=forms.TextInput(attrs={"class": "input"}),
    )
    payment_callback_url = forms.URLField(
        label="URL callback платежей",
        required=False,
        widget=forms.URLInput(attrs={"class": "input"}),
    )
    email_from = forms.EmailField(
        label="Email отправителя",
        required=False,
        widget=forms.EmailInput(attrs={"class": "input"}),
    )
    terms_of_use = forms.CharField(
        label="Пользовательское соглашение (текст)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6, "class": "input"}),
    )
    privacy_policy = forms.CharField(
        label="Политика конфиденциальности (текст)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6, "class": "input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_api_key"].initial = SiteSetting.get("payment_api_key")
        self.fields["payment_callback_url"].initial = SiteSetting.get("payment_callback_url")
        self.fields["email_from"].initial = SiteSetting.get("email_from")
        self.fields["terms_of_use"].initial = SiteSetting.get("terms_of_use")
        self.fields["privacy_policy"].initial = SiteSetting.get("privacy_policy")

    def save(self):
        for key in [
            "payment_api_key",
            "payment_callback_url",
            "email_from",
            "terms_of_use",
            "privacy_policy",
        ]:
            SiteSetting.set(key, self.cleaned_data.get(key, "") or "")


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "description", "sort_order"]

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip().lower()
        if not slug:
            raise ValidationError("Слаг обязателен.")
        if not SLUG_RE.match(slug):
            raise ValidationError("Слаг может содержать только латинские буквы, цифры и дефис.")
        qs = Category.objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Категория с таким слагом уже существует.")
        return slug

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise ValidationError("Название обязательно.")
        return name


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "slug",
            "short_description",
            "description",
            "price",
            "product_type",
            "license_type",
            "purpose",
            "status",
        ]

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip().lower()
        if not slug:
            raise ValidationError("Слаг обязателен.")
        if not SLUG_RE.match(slug):
            raise ValidationError("Слаг может содержать только латинские буквы, цифры и дефис.")
        qs = Product.objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Товар с таким слагом уже существует.")
        return slug

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise ValidationError("Цена не может быть отрицательной.")
        return price

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise ValidationError("Название обязательно.")
        return name

    def clean_category(self):
        category = self.cleaned_data.get("category")
        if not category:
            raise ValidationError("Выберите категорию.")
        return category


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "is_active", "role"]


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status"]


class DigitalItemForm(forms.ModelForm):
    class Meta:
        model = DigitalItem
        fields = ["item_type", "value", "max_activations", "status"]


class ProductMediaForm(forms.ModelForm):
    class Meta:
        model = ProductMedia
        fields = ["media_type", "url", "sort_order"]

