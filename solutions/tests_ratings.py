from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from solutions.models import Solution
from solutions.ratings import Rating

User = get_user_model()


class RatingModelTests(TestCase):
    """Tests for the Rating model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.solution = Solution.objects.create(
            title='Test Solution',
            content='This is a test solution',
            author=self.user
        )
        self.rating = Rating.objects.create(
            solution=self.solution,
            user=self.user,
            value=4
        )

    def test_rating_creation(self):
        """Test rating can be created."""
        self.assertEqual(self.rating.value, 4)
        self.assertEqual(self.rating.user, self.user)
        self.assertEqual(self.rating.solution, self.solution)

    def test_rating_str_representation(self):
        """Test rating string representation."""
        expected = f'{self.user.username} rated {self.solution.title}: {self.rating.value}/5'
        self.assertEqual(str(self.rating), expected)

    def test_unique_constraint(self):
        """Test that a user can only have one rating per solution."""
        with self.assertRaises(Exception):
            Rating.objects.create(
                solution=self.solution,
                user=self.user,
                value=3  # Different rating value
            )


class RatingFunctionsTests(TestCase):
    """Tests for the solution rating functions."""

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.user3 = User.objects.create_user(username='user3', password='pass123')

        self.solution = Solution.objects.create(
            title='Test Solution',
            content='Test content',
            author=self.user1
        )

        Rating.objects.create(solution=self.solution, user=self.user1, value=5)
        Rating.objects.create(solution=self.solution, user=self.user2, value=3)
        Rating.objects.create(solution=self.solution, user=self.user3, value=4)

    def test_get_average_rating(self):
        """Test calculating average rating."""
        self.assertEqual(self.solution.get_average_rating(), 4.0)

    def test_get_rating_count(self):
        """Test counting ratings."""
        self.assertEqual(self.solution.get_rating_count(), 3)

    def test_user_has_rated(self):
        """Test checking if user has already rated."""
        self.assertTrue(self.solution.user_has_rated(self.user1))
        self.assertTrue(self.solution.user_has_rated(self.user2))

        new_user = User.objects.create_user(username='newuser', password='pass123')
        self.assertFalse(self.solution.user_has_rated(new_user))

    def test_get_user_rating(self):
        """Test retrieving a user's specific rating."""
        self.assertEqual(self.solution.get_user_rating(self.user1), 5)
        self.assertEqual(self.solution.get_user_rating(self.user2), 3)

        new_user = User.objects.create_user(username='newuser', password='pass123')
        self.assertIsNone(self.solution.get_user_rating(new_user))


class RatingViewsTests(TestCase):
    """Tests for the rating views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.solution = Solution.objects.create(
            title='Test Solution',
            content='This is a test solution',
            author=self.user
        )
        self.rate_url = reverse('solutions:rate', args=[self.solution.slug])
        self.unrate_url = reverse('solutions:unrate', args=[self.solution.slug])

    def test_rate_solution_view(self):
        """Test rating a solution."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.rate_url, {'value': 4})
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(Rating.objects.first().value, 4)

    def test_update_rating_view(self):
        """Test updating an existing rating."""
        # First create a rating
        Rating.objects.create(solution=self.solution, user=self.user, value=3)

        # Then update it
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.rate_url, {'value': 5})
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Rating.objects.count(), 1)  # Count should remain 1
        self.assertEqual(Rating.objects.first().value, 5)  # Value should be updated

    def test_delete_rating_view(self):
        """Test removing a rating."""
        # First create a rating
        Rating.objects.create(solution=self.solution, user=self.user, value=3)

        # Then delete it
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.unrate_url)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Rating.objects.count(), 0)

    def test_rating_view_authentication(self):
        """Test that unauthorized users can't add ratings."""
        # Test with anonymous user
        response = self.client.post(self.rate_url, {'value': 4})
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertEqual(Rating.objects.count(), 0)  # Rating count unchanged
