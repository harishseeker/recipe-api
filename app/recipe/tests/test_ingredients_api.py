from django.contrib.auth import get_user_model
from django.urls import reverse

from django.test import TestCase

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

from rest_framework.test import APIClient
from rest_framework import status

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='test@example.com', password='testpass123'):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientAPITests(TestCase):
    def test_auth_required(self):
        client = APIClient()
        res = client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngreidentAPITests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrive_ingredients(self):
        Ingredient.objects.create(
            user=self.user,
            name='Tomato',
        )
        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        other_user = get_user_model().objects.create_user(
            email='otheruser@example.com',
            password='testpass12345',
        )

        Ingredient.objects.create(user=other_user, name='Tomato')
        Ingredient.objects.create(user=other_user, name='Tamarind')

        ingredient = Ingredient.objects.create(user=self.user, name='Cabbage')

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_ingredient_update(self):
        ingredient = Ingredient.objects.create(user=self.user, name='mutton')

        payload = {'name': 'fish'}
        url = detail_url(ingredient.id)

        res = self.client.patch(url, payload)
        ingredient.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.name, payload['name'])

    def test_ingredient_delete(self):
        ingredient = Ingredient.objects.create(user=self.user, name='Papaya')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())
