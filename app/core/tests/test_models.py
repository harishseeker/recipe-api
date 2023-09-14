from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models
from decimal import Decimal
from unittest.mock import patch


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

    def test_create_recipe(self):
        user = get_user_model().objects.create_user(
            'testrecipe@example.com',
            'testpass123',
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Onion',
        )
        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
