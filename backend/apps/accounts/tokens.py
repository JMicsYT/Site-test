from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Генератор токенов подтверждения email на базе стандартного механизма Django.
    """

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.email_verified}"


email_verification_token = EmailVerificationTokenGenerator()

