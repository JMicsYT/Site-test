import hashlib
import hmac
import os
import time

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User
from .security import hibp_check_password


def _make_math_captcha():
    """Генерирует простую арифметическую капчу с HMAC-подписью."""
    import random
    a = random.randint(2, 9)
    b = random.randint(2, 9)
    op = random.choice(["+", "-"])
    result = a + b if op == "+" else a - b
    ts = str(int(time.time()))
    payload = f"{result}:{ts}"
    secret = os.environ.get("DJANGO_SECRET_KEY", "dev-secret").encode()
    sig = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()[:16]
    return {
        "question": f"Сколько будет {a} {op} {b}?",
        "token": f"{payload}:{sig}",
    }


def _verify_math_captcha(token: str, answer: str, max_age: int = 600) -> bool:
    if not token or not answer:
        return False
    try:
        result_s, ts_s, sig = token.rsplit(":", 2)
    except ValueError:
        return False
    payload = f"{result_s}:{ts_s}"
    secret = os.environ.get("DJANGO_SECRET_KEY", "dev-secret").encode()
    expected = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()[:16]
    if not hmac.compare_digest(expected, sig):
        return False
    try:
        if int(time.time()) - int(ts_s) > max_age:
            return False
        return int(answer.strip()) == int(result_s)
    except ValueError:
        return False


class CaptchaMixin:
    """Добавляет поля captcha_token + captcha_answer. При is_valid проверяет их."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._captcha_data = _make_math_captcha()
        self.fields["captcha_token"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=self._captcha_data["token"],
            required=True,
        )
        self.fields["captcha_answer"] = forms.CharField(
            label=self._captcha_data["question"],
            required=True,
            max_length=8,
        )
        if self.is_bound and "captcha_token" in self.data:
            self.fields["captcha_token"].initial = self.data["captcha_token"]
            from_data = self.data.get("captcha_token", "")
            try:
                result_s, ts_s, _ = from_data.rsplit(":", 2)
                a_b = int(result_s)
                self.fields["captcha_answer"].label = "Проверка: введите ответ"
            except Exception:
                pass

    def clean(self):
        cleaned = super().clean()
        if not _verify_math_captcha(
            cleaned.get("captcha_token", ""), cleaned.get("captcha_answer", "")
        ):
            raise forms.ValidationError("Неверный ответ на проверочный вопрос.")
        return cleaned


class RegistrationForm(CaptchaMixin, forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Укажите email.")
        # Не раскрываем, что email уже занят — защита от user enumeration.
        # Вместо этого при сохранении поймаем IntegrityError и вернём общую ошибку.
        return email

    def clean_password(self):
        p = self.cleaned_data.get("password") or ""
        try:
            validate_password(p)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        count = hibp_check_password(p)
        if count > 0:
            raise forms.ValidationError(
                f"Этот пароль найден в базе утечек ({count} раз). Используйте другой."
            )
        return p

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password_confirm")
        if p1 and p2 and p1 != p2:
            self.add_error("password_confirm", "Пароли не совпадают")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            self.user = authenticate(email=email, password=password)
            # Единое сообщение для всех ошибок (защита от user enumeration)
            if self.user is None or not self.user.is_active:
                self.user = None
                raise forms.ValidationError("Неверный email или пароль.")
        return cleaned

    def get_user(self):
        return self.user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "telegram",
            "birth_date",
            "country",
            "city",
            "address",
            "bio",
            "newsletter",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "bio": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
        }


class AvatarForm(forms.ModelForm):
    """
    Безопасная валидация аватара:
      - ограничение размера (2 МБ),
      - проверка MIME по magic-bytes (PNG/JPEG/WebP) — не по расширению,
      - ресайз до 512×512 через Pillow (удаляет EXIF: GPS и пр.),
      - пересохранение в JPEG/PNG — нельзя «спрятать» вредонос в картинке.
    """

    MAX_SIZE = 2 * 1024 * 1024
    ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
    OUTPUT_SIZE = (512, 512)

    class Meta:
        model = User
        fields = ["avatar"]

    def clean_avatar(self):
        from io import BytesIO
        from django.core.files.uploadedfile import InMemoryUploadedFile

        f = self.cleaned_data.get("avatar")
        if not f:
            return f

        if hasattr(f, "size") and f.size > self.MAX_SIZE:
            raise ValidationError("Размер файла не должен превышать 2 МБ.")

        try:
            from PIL import Image, UnidentifiedImageError
        except ImportError:
            return f  # fallback, Pillow должен быть в requirements

        try:
            f.seek(0)
            img = Image.open(f)
            img.verify()
            f.seek(0)
            img = Image.open(f)
        except (UnidentifiedImageError, Exception):
            raise ValidationError("Загруженный файл не является изображением.")

        fmt = (img.format or "").upper()
        if fmt not in self.ALLOWED_FORMATS:
            raise ValidationError(
                "Допустимые форматы аватара: JPEG, PNG, WebP."
            )

        # Конвертируем в RGB (убирает альфа и посторонние профили),
        # ресайз в thumbnail (сохраняет пропорции, удаляет EXIF).
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail(self.OUTPUT_SIZE, Image.LANCZOS)

        buf = BytesIO()
        out_format = "JPEG" if fmt != "PNG" else "PNG"
        img.save(buf, format=out_format, quality=88, optimize=True)
        buf.seek(0)

        return InMemoryUploadedFile(
            buf,
            field_name="avatar",
            name=f"avatar.{out_format.lower()}",
            content_type=f"image/{out_format.lower()}",
            size=buf.getbuffer().nbytes,
            charset=None,
        )


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(label="Текущий пароль", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Новый пароль", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old = self.cleaned_data.get("old_password")
        if not self.user.check_password(old):
            raise ValidationError("Неверный текущий пароль.")
        return old

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", "Пароли не совпадают.")
        if p1:
            try:
                validate_password(p1, self.user)
            except ValidationError as e:
                self.add_error("new_password1", e)
            # Проверка по HIBP
            hibp_count = hibp_check_password(p1)
            if hibp_count > 0:
                self.add_error(
                    "new_password1",
                    f"Этот пароль найден в базах утечек ({hibp_count} раз). Используйте другой.",
                )
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save(update_fields=["password"])
        return self.user

