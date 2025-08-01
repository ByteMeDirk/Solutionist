from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.test import TestCase
from django.urls import reverse

from comments.models import Comment
from solutions.models import Solution
from solutions.ratings import Rating
from tags.models import Tag

User = get_user_model()


class SolutionSearchTests(TestCase):
    """Tests for the solution search functionality."""

    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")

        # Create tags
        self.tag_python = Tag.objects.create(name="Python")
        self.tag_django = Tag.objects.create(name="Django")
        self.tag_aws = Tag.objects.create(name="AWS")

        # Create solutions
        self.solution1 = Solution.objects.create(
            title="Django REST API",
            content="How to build a Django REST API",
            author=self.user1,
        )
        self.solution1.tags.add(self.tag_django, self.tag_python)

        self.solution2 = Solution.objects.create(
            title="AWS Lambda Functions",
            content="Deploying Python functions to AWS Lambda",
            author=self.user1,
        )
        self.solution2.tags.add(self.tag_aws, self.tag_python)

        self.solution3 = Solution.objects.create(
            title="Django Templates",
            content="Working with Django template system",
            author=self.user2,
        )
        self.solution3.tags.add(self.tag_django)

        # Add some ratings
        Rating.objects.create(solution=self.solution1, user=self.user1, value=5)
        Rating.objects.create(solution=self.solution1, user=self.user2, value=4)
        Rating.objects.create(solution=self.solution2, user=self.user2, value=3)
        Rating.objects.create(solution=self.solution3, user=self.user1, value=2)

        # Add some comments
        Comment.objects.create(
            solution=self.solution1, author=self.user2, content="Great tutorial!"
        )
        Comment.objects.create(
            solution=self.solution2, author=self.user1, content="Very helpful"
        )

        # Set view counts
        self.solution1.view_count = 15
        self.solution1.save()
        self.solution2.view_count = 10
        self.solution2.save()
        self.solution3.view_count = 5
        self.solution3.save()

        # URL for solution list
        self.list_url = reverse("solutions:list")

    def test_search_by_text(self):
        """Test searching solutions by text."""
        # Search for 'REST'
        response = self.client.get(f"{self.list_url}?query=REST")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django REST API")
        self.assertNotContains(response, "AWS Lambda Functions")
        self.assertNotContains(response, "Django Templates")

    def test_filter_by_tag(self):
        """Test filtering solutions by tag."""
        # Filter by 'Django' tag
        response = self.client.get(f"{self.list_url}?tags=Django")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django REST API")
        self.assertContains(response, "Django Templates")
        self.assertNotContains(response, "AWS Lambda Functions")

        # Filter by 'AWS' tag
        response = self.client.get(f"{self.list_url}?tags=AWS")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AWS Lambda Functions")
        self.assertNotContains(response, "Django REST API")
        self.assertNotContains(response, "Django Templates")

    def test_sort_by_date(self):
        """Test sorting solutions by date."""
        # Most recent first (default)
        response = self.client.get(f"{self.list_url}?sort_by=date_desc")
        self.assertEqual(response.status_code, 200)
        solutions = response.context["page_obj"]
        self.assertEqual(
            solutions[0], self.solution3
        )  # Assuming solution3 was created last

        # Oldest first
        response = self.client.get(f"{self.list_url}?sort_by=date_asc")
        self.assertEqual(response.status_code, 200)
        solutions = response.context["page_obj"]
        self.assertEqual(
            solutions[0], self.solution1
        )  # Assuming solution1 was created first

    def test_sort_by_rating(self):
        """Test sorting solutions by rating."""
        # Highest rated first
        response = self.client.get(f"{self.list_url}?sort_by=rating_desc")
        self.assertEqual(response.status_code, 200)
        solutions = response.context["page_obj"]

        # Calculate average ratings manually to verify
        avg_ratings = {
            solution.id: solution.ratings.aggregate(avg=Avg("value"))["avg"]
            for solution in Solution.objects.all()
        }

        # Find solution with highest rating
        highest_rated_id = max(avg_ratings, key=avg_ratings.get)
        self.assertEqual(solutions[0].id, highest_rated_id)

    def test_sort_by_views(self):
        """Test sorting solutions by view count."""
        response = self.client.get(f"{self.list_url}?sort_by=views_desc")
        self.assertEqual(response.status_code, 200)
        solutions = response.context["page_obj"]
        self.assertEqual(solutions[0], self.solution1)  # solution1 has most views (15)
        self.assertEqual(solutions[1], self.solution2)  # solution2 has 10 views
        self.assertEqual(solutions[2], self.solution3)  # solution3 has 5 views

    def test_combined_search(self):
        """Test combining search text, tags, and sorting."""
        # Search for Python solutions, sorted by rating
        response = self.client.get(
            f"{self.list_url}?query=Python&tags=Python&sort_by=rating_desc"
        )
        self.assertEqual(response.status_code, 200)
        solutions = response.context["page_obj"]
        # Should only contain Python-tagged solutions
        for solution in solutions:
            self.assertTrue(self.tag_python in solution.tags.all())


class SolutionRatingIntegrationTests(TestCase):
    """Integration tests for solutions with ratings."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.solution = Solution.objects.create(
            title="Integration Test Solution",
            content="Content for integration testing",
            author=self.user,
        )
        self.detail_url = reverse("solutions:detail", args=[self.solution.slug])

    def test_rating_displayed_in_detail_view(self):
        """Test that ratings are displayed in solution detail view."""
        # First no ratings
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No ratings yet")

        # Add ratings
        Rating.objects.create(solution=self.solution, user=self.user, value=4)

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "4.0")  # Should display the rating value
        self.assertContains(response, "(1 rating)")  # Should show rating count

    def test_comment_displayed_in_detail_view(self):
        """Test that comments are displayed in solution detail view."""
        # First no comments
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No comments yet")

        # Add a comment
        Comment.objects.create(
            solution=self.solution, author=self.user, content="Test comment"
        )

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test comment")
        self.assertContains(response, "Comments (1)")  # Should show comment count
