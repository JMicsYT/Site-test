from django.test import TestCase, Client
from django.urls import reverse

from .models import SecurityEvent


class SecurityEventTests(TestCase):
    def test_security_event_creation(self):
        event = SecurityEvent.objects.create(
            event_type="login_failed",
            description="Test",
            ip_address="127.0.0.1",
        )
        self.assertEqual(event.event_type, "login_failed")
        self.assertIsNotNone(event.created_at)
