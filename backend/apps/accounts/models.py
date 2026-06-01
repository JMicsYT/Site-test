import secrets

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.USER)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        USER = "user", "Пользователь"
        ADMIN = "admin", "Администратор"

    email = models.EmailField("Email", unique=True, db_index=True)
    first_name = models.CharField("Имя", max_length=150, blank=True)
    last_name = models.CharField("Фамилия", max_length=150, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    avatar = models.ImageField(
        "Аватар", upload_to="avatars/", blank=True, null=True
    )
    bio = models.TextField("О себе", max_length=500, blank=True)
    birth_date = models.DateField("Дата рождения", blank=True, null=True)
    country = models.CharField("Страна", max_length=80, blank=True)
    city = models.CharField("Город", max_length=80, blank=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    telegram = models.CharField("Telegram", max_length=64, blank=True)
    newsletter = models.BooleanField("Подписан на рассылку", default=False)
    date_joined = models.DateTimeField("Дата регистрации", default=timezone.now)
    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Персонал", default=False)
    email_verified = models.BooleanField("Email подтверждён", default=False)
    role = models.CharField(
        "Роль",
        max_length=16,
        choices=Role.choices,
        default=Role.USER,
        db_index=True,
    )

    # ===== Безопасность =====
    # 2FA (TOTP)
    totp_secret = models.CharField("TOTP-секрет", max_length=64, blank=True)
    totp_enabled = models.BooleanField("2FA включена", default=False)
    backup_codes = models.JSONField("Коды восстановления (хэши)", default=list, blank=True)

    # Блокировка после неудачных попыток
    failed_login_attempts = models.PositiveIntegerField("Неуспешных попыток входа", default=0)
    locked_until = models.DateTimeField("Заблокирован до", null=True, blank=True)
    unlock_token = models.CharField("Токен разблокировки", max_length=64, blank=True)

    # Последний вход
    last_login_ip = models.GenericIPAddressField("IP последнего входа", null=True, blank=True)
    last_login_ua = models.CharField("User-Agent последнего входа", max_length=512, blank=True)

    # ===== Реферальная программа =====
    referral_code = models.CharField(
        "Реферальный код", max_length=16, unique=True, blank=True, db_index=True,
    )
    referred_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="referrals",
        verbose_name="Пригласивший",
    )
    referral_bonus_paid = models.BooleanField(
        "Реферальный бонус пригласившему выплачен", default=False,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email.split("@")[0]

    @property
    def initials(self) -> str:
        parts = [p for p in [self.first_name, self.last_name] if p]
        if parts:
            return "".join(p[0].upper() for p in parts[:2])
        return self.email[:2].upper()

    def is_locked(self) -> bool:
        """Проверка временной блокировки аккаунта (account lockout)."""
        return bool(self.locked_until and self.locked_until > timezone.now())

    def generate_unlock_token(self) -> str:
        """Генерирует токен для разблокировки по ссылке из письма."""
        self.unlock_token = secrets.token_urlsafe(32)
        return self.unlock_token

    def ensure_referral_code(self) -> str:
        """Гарантирует наличие уникального реферального кода."""
        if self.referral_code:
            return self.referral_code
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        for _ in range(10):
            code = "".join(secrets.choice(alphabet) for _ in range(8))
            if not User.objects.filter(referral_code=code).exists():
                self.referral_code = code
                return code
        self.referral_code = secrets.token_urlsafe(8)[:16]
        return self.referral_code

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.ensure_referral_code()
        super().save(*args, **kwargs)

