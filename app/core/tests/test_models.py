from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = 'invento@example.com'
        password = 'raviashwin'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_email_normalized(self):
        sample_emails = [
            ['TEST1@EXAMPLE.COM', 'TEST1@example.com'],
            ['Test2@example.com', 'Test2@example.com'],
            ['test3@example.COM', 'test3@example.com']
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_create_user_without_email_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'sample123')

    def test_superuser(self):
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'raviashwin',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
