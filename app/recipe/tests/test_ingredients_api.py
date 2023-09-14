from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal

from django.test import TestCase

from core.models import Ingredient, Recipe
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

    def test_filter_ingredients_assigned_to_recipe(self):
        i1 = Ingredient.objects.create(user=self.user, name='Ice cream')
        i2 = Ingredient.objects.create(user=self.user, name='Mango')
        recipe = Recipe.objects.create(
            user=self.user,
            title='milk shake',
            time_minutes=15,
            price=Decimal('3.25'),
        )
        recipe.ingredients.add(i1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        s1 = IngredientSerializer(i1)
        s2 = IngredientSerializer(i2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def filtered_unique_ingredients(self):
        ing = Ingredient.objects.create(user=self.user, name='Milk')
        Ingredient.objects.create(user=self.user, name='Butter')
        r1 = Recipe.objects.create(
            user=self.user,
            title='milk shake',
            time_minutes=15,
            price=Decimal('3.25'),
        )
        r2 = Recipe.objects.create(
            user=self.user,
            title='payasam',
            time_minutes=45,
            price=Decimal('5.25'),
        )
        r1.ingredients.add(ing)
        r2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
