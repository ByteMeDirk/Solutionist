from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from solutions.models import Solution

from .models import Comment

User = get_user_model()


class CommentModelTests(TestCase):
    """Tests for the Comment model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.solution = Solution.objects.create(
            title="Test Solution", content="This is a test solution", author=self.user
        )
        self.comment = Comment.objects.create(
            solution=self.solution, author=self.user, content="This is a test comment"
        )

    def test_comment_creation(self):
        """Test comment can be created."""
        self.assertEqual(self.comment.content, "This is a test comment")
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.solution, self.solution)
        self.assertIsNone(self.comment.parent)
        self.assertTrue(self.comment.is_active)

    def test_comment_str_representation(self):
        """Test comment string representation."""
        expected = f"Comment by {self.user.username} on {self.solution.title}"
        self.assertEqual(str(self.comment), expected)

    def test_comment_reply(self):
        """Test reply to comment."""
        reply = Comment.objects.create(
            solution=self.solution,
            author=self.user,
            parent=self.comment,
            content="This is a reply",
        )
        self.assertEqual(reply.parent, self.comment)
        self.assertEqual(self.comment.replies.count(), 1)
        self.assertEqual(self.comment.replies.first(), reply)


class CommentViewTests(TestCase):
    """Tests for the Comment views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.solution = Solution.objects.create(
            title="Test Solution", content="This is a test solution", author=self.user
        )
        self.comment = Comment.objects.create(
            solution=self.solution, author=self.user, content="This is a test comment"
        )
        self.add_comment_url = reverse(
            "comments:add_comment", args=[self.solution.slug]
        )
        self.add_reply_url = reverse(
            "comments:add_reply", args=[self.solution.slug, self.comment.id]
        )
        self.delete_comment_url = reverse(
            "comments:delete_comment", args=[self.comment.id]
        )

    def test_add_comment_view(self):
        """Test adding a new comment."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.add_comment_url, {"content": "New comment"})
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(Comment.objects.latest("created_at").content, "New comment")

    def test_add_reply_view(self):
        """Test adding a reply to a comment."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.add_reply_url, {"content": "New reply"})
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Comment.objects.count(), 2)
        reply = Comment.objects.latest("created_at")
        self.assertEqual(reply.content, "New reply")
        self.assertEqual(reply.parent, self.comment)

    def test_delete_comment_view(self):
        """Test deleting a comment."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.delete_comment_url)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_view_authentication(self):
        """Test that unauthorized users can't add or delete comments."""
        # Test with anonymous user
        response = self.client.post(
            self.add_comment_url, {"content": "Anonymous comment"}
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertEqual(Comment.objects.count(), 1)  # Comment count unchanged

        # Test with different user
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.post(self.delete_comment_url)
        self.assertEqual(
            response.status_code, 404
        )  # Not found, as the comment doesn't belong to this user
        self.assertEqual(Comment.objects.count(), 1)  # Comment count unchanged
