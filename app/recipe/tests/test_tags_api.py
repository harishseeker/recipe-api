from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer
from decimal import Decimal

TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='test@example.com', password='testpass123'):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITest(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrive_tags(self):
        Tag.objects.create(user=self.user, name='Non-Veg')
        Tag.objects.create(user=self.user, name='Veg')

        res = self.client.get(TAGS_URL)

        tag = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tag, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tag_limited_to_user(self):
        other_user = get_user_model().objects.create_user(
            email='otheruser@example.com', password='testpass123'
        )
        Tag.objects.create(user=other_user, name='Dessert')
        Tag.objects.create(user=other_user, name='Starter')

        tag = Tag.objects.create(user=self.user, name='Non-Veg')

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        tag = Tag.objects.create(user=self.user, name='Chinese')

        payload = {'name': 'Thai'}
        res = self.client.patch(detail_url(tag.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        tag = Tag.objects.create(user=self.user, name='Chettinad')

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Tag.objects.filter(user=self.user).exists())

    def test_filter_tags_assigned_to_recipe(self):
        t1 = Tag.objects.create(user=self.user, name='Non-Veg')
        t2 = Tag.objects.create(user=self.user, name='Veg')

        recipe = Recipe.objects.create(
            user=self.user,
            title='sambar',
            time_minutes=30,
            price=Decimal('3.15'),
        )
        recipe.tags.add(t1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        s1 = TagSerializer(t1)
        s2 = TagSerializer(t2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_unique_tags(self):
        tag = Tag.objects.create(user=self.user, name='Dinner')
        Tag.objects.create(user=self.user, name='Lunch')
        r1 = Recipe.objects.create(
            user=self.user,
            title='chapathi',
            time_minutes=30,
            price=Decimal('2.15'),
        )
        r2 = Recipe.objects.create(
            user=self.user,
            title='butter chicken',
            time_minutes=40,
            price=Decimal('8.15'),
        )
        r1.tags.add(tag)
        r2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
