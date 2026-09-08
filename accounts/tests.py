from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


class CustomUserTests(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="Testuser",
            email="test123@email.com",
            password="password123",
        )

        self.assertEqual(user.username, "Testuser")
        self.assertEqual(user.email, "test123@email.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            username="Testadmin",
            email="Admin123@email.com",
            password="Password123",
        )

        self.assertEqual(admin_user.username, "Testadmin")
        self.assertEqual(admin_user.email, "Admin123@email.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
    SECURE_HSTS_SECONDS=0,
)
class SignupPageTests(TestCase):
    username = "newuser"
    email = "newuser@email.com"

    def setUp(self):
        url = reverse("account_signup")
        self.response = self.client.get(url)

    def test_signup_templates(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, "account/signup.html")
        self.assertContains(self.response, "Sign Up")
        self.assertNotContains(self.response, "This should not be on the page")

    def test_signup_form(self):
        new_user = get_user_model().objects.create_user(self.username, self.email)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(new_user.username, self.username)
        self.assertEqual(new_user.email, self.email)
