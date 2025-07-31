from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from solutions.models import Solution
from .models import Tag

User = get_user_model()


class TagModelTests(TestCase):
    """Tests for the Tag model."""

    def setUp(self):
        self.tag = Tag.objects.create(name='Python', description='Python programming language')

    def test_tag_creation(self):
        """Test tag can be created."""
        self.assertEqual(self.tag.name, 'Python')
        self.assertEqual(self.tag.description, 'Python programming language')
        self.assertEqual(self.tag.slug, 'python')

    def test_tag_str_representation(self):
        """Test tag string representation."""
        self.assertEqual(str(self.tag), 'Python')

    def test_unique_name(self):
        """Test that tag names are unique."""
        with self.assertRaises(Exception):
            Tag.objects.create(name='Python', description='Another description')

    def test_auto_slug_generation(self):
        """Test slug is automatically generated from name."""
        tag = Tag.objects.create(name='Django REST Framework')
        self.assertEqual(tag.slug, 'django-rest-framework')


class TagViewTests(TestCase):
    """Tests for the Tag views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tag1 = Tag.objects.create(name='Python', description='Python programming language')
        self.tag2 = Tag.objects.create(name='Django', description='Django web framework')

        # Create some solutions with tags
        self.solution1 = Solution.objects.create(
            title='Python Solution',
            content='This is a Python solution',
            author=self.user
        )
        self.solution1.tags.add(self.tag1)

        self.solution2 = Solution.objects.create(
            title='Django Solution',
            content='This is a Django solution',
            author=self.user
        )
        self.solution2.tags.add(self.tag2)

        self.solution3 = Solution.objects.create(
            title='Python Django Solution',
            content='This is a Python and Django solution',
            author=self.user
        )
        self.solution3.tags.add(self.tag1, self.tag2)

        self.tag_list_url = reverse('tags:list')
        self.tag_detail_url = reverse('tags:detail', args=[self.tag1.slug])
        self.tag_autocomplete_url = reverse('tags:autocomplete')

    def test_tag_list_view(self):
        """Test tag list view."""
        response = self.client.get(self.tag_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python')
        self.assertContains(response, 'Django')

    def test_tag_detail_view(self):
        """Test tag detail view."""
        response = self.client.get(self.tag_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python')
        self.assertContains(response, 'Python Solution')
        self.assertContains(response, 'Python Django Solution')
        self.assertNotContains(response, 'Django Solution')  # This solution has only Django tag

    def test_tag_autocomplete(self):
        """Test tag autocomplete view."""
        # Test with query that should match Python
        response = self.client.get(f'{self.tag_autocomplete_url}?q=py')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'results': [{'id': self.tag1.id, 'text': 'Python'}]}
        )

        # Test with query that should match Django
        response = self.client.get(f'{self.tag_autocomplete_url}?q=dja')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'results': [{'id': self.tag2.id, 'text': 'Django'}]}
        )

        # Test with query that should match both
        response = self.client.get(f'{self.tag_autocomplete_url}?q=p')
        self.assertEqual(response.status_code, 200)
        # Should have two results but order might vary, so test length
        result = response.json()
        self.assertEqual(len(result['results']), 1)  # Only Python starts with 'p'
