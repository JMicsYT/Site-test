from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from shoshop.celery import app

from .tokens import email_verification_token


User = get_user_model()


def _do_send_email_verification(user_id):
    """Общая логика отправки письма подтверждения (для задачи и для синхронного вызова)."""
    user = User.objects.get(pk=user_id)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    domain = settings.DEFAULT_DOMAIN or "127.0.0.1:8000"
    protocol = "http" if settings.DEBUG else "https"
    verify_url = f"{protocol}://{domain}/accounts/verify-email/{uid}/{token}/"
    subject = "Подтверждение email на ShoShop"
    message = render_to_string(
        "accounts/email_verification.txt",
        {"user": user, "verify_url": verify_url},
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


@app.task
def send_email_verification(user_id):
    _do_send_email_verification(user_id)


def send_email_verification_sync(user_id):
    """Синхронная отправка (для локального запуска без Celery/Redis)."""
    _do_send_email_verification(user_id)


def _do_send_account_unlock(user_id):
    user = User.objects.get(pk=user_id)
    if not user.unlock_token:
        return
    domain = settings.DEFAULT_DOMAIN or "127.0.0.1:8000"
    protocol = "http" if settings.DEBUG else "https"
    unlock_url = f"{protocol}://{domain}/accounts/unlock/{user.unlock_token}/"
    subject = "Ваш аккаунт ShoShop временно заблокирован"
    message = (
        f"Здравствуйте, {user.full_name}.\n\n"
        f"Мы зафиксировали несколько неудачных попыток входа в ваш аккаунт. "
        f"В целях безопасности он временно заблокирован.\n\n"
        f"Если это были вы — подождите окончания блокировки или перейдите "
        f"по ссылке, чтобы разблокировать аккаунт немедленно:\n\n"
        f"{unlock_url}\n\n"
        f"Если вы не пытались войти — смените пароль при следующем входе.\n\n"
        f"— Команда ShoShop"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


@app.task
def send_account_unlock_email(user_id):
    _do_send_account_unlock(user_id)


def send_account_unlock_email_sync(user_id):
    _do_send_account_unlock(user_id)

