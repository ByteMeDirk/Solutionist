from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from tags.models import Tag

from .forms import SolutionForm
from .models import Solution, SolutionVersion


class SolutionModelTests(TestCase):
    """
    Tests for the Solution model.
    """

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="StrongPassword123"
        )

        # Create a test tag
        self.tag = Tag.objects.create(name="Test Tag")

        # Create a test solution
        self.solution = Solution.objects.create(
            title="Test Solution",
            content="# Test Content\n\nThis is a test solution.",
            author=self.user,
        )
        self.solution.tags.add(self.tag)

    def test_solution_creation(self):
        """Test that a solution can be created with the correct attributes."""
        self.assertEqual(self.solution.title, "Test Solution")
        self.assertEqual(
            self.solution.content, "# Test Content\n\nThis is a test solution."
        )
        self.assertEqual(self.solution.author, self.user)
        self.assertTrue(self.solution.is_published)
        self.assertEqual(self.solution.view_count, 0)

        # Check that the solution has the correct tag
        self.assertEqual(self.solution.tags.count(), 1)
        self.assertEqual(self.solution.tags.first(), self.tag)

        # Check that the content_html field is populated
        self.assertIn(
            '<h1 id="test-content">Test Content</h1>', self.solution.content_html
        )

    def test_solution_slug_generation(self):
        """Test that a slug is automatically generated from the title."""
        self.assertEqual(self.solution.slug, "test-solution")

        # Test that slugs are unique
        solution2 = Solution.objects.create(
            title="Test Solution", content="Another test solution.", author=self.user
        )
        self.assertEqual(solution2.slug, "test-solution-1")

    def test_get_absolute_url(self):
        """Test that get_absolute_url returns the correct URL."""
        expected_url = reverse("solutions:detail", kwargs={"slug": self.solution.slug})
        self.assertEqual(self.solution.get_absolute_url(), expected_url)

    def test_increment_view_count(self):
        """Test that increment_view_count increases the view count."""
        self.assertEqual(self.solution.view_count, 0)
        self.solution.increment_view_count()
        self.assertEqual(self.solution.view_count, 1)
        self.solution.increment_view_count()
        self.assertEqual(self.solution.view_count, 2)


class SolutionVersionModelTests(TestCase):
    """
    Tests for the SolutionVersion model.
    """

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="StrongPassword123"
        )

        # Create a test solution
        self.solution = Solution.objects.create(
            title="Test Solution",
            content="# Initial Content\n\nThis is the initial version.",
            author=self.user,
        )

        # Create an initial version (should be created automatically)
        self.initial_version = SolutionVersion.objects.create(
            solution=self.solution,
            content=self.solution.content,
            created_by=self.user,
            change_comment="Initial version",
        )

    def test_version_creation(self):
        """Test that a version can be created with the correct attributes."""
        self.assertEqual(self.initial_version.solution, self.solution)
        self.assertEqual(
            self.initial_version.content,
            "# Initial Content\n\nThis is the initial version.",
        )
        self.assertEqual(self.initial_version.created_by, self.user)
        self.assertEqual(self.initial_version.change_comment, "Initial version")
        self.assertEqual(self.initial_version.version_number, 1)

    def test_version_auto_increment(self):
        """Test that version numbers are automatically incremented."""
        # Create a second version
        version2 = SolutionVersion.objects.create(
            solution=self.solution,
            content="# Updated Content\n\nThis is the second version.",
            created_by=self.user,
            change_comment="Updated content",
        )
        self.assertEqual(version2.version_number, 2)

        # Create a third version
        version3 = SolutionVersion.objects.create(
            solution=self.solution,
            content="# Updated Again\n\nThis is the third version.",
            created_by=self.user,
            change_comment="Updated again",
        )
        self.assertEqual(version3.version_number, 3)

    def test_get_diff_to_previous(self):
        """Test that get_diff_to_previous returns a diff between versions."""
        # Create a second version
        version2 = SolutionVersion.objects.create(
            solution=self.solution,
            content="# Updated Content\n\nThis is the second version.",
            created_by=self.user,
            change_comment="Updated content",
        )

        # Get the diff
        diff = version2.get_diff_to_previous()

        # Check that the diff contains the expected changes
        self.assertIn("-# Initial Content", diff)
        self.assertIn("+# Updated Content", diff)
        self.assertIn("-This is the initial version.", diff)
        self.assertIn("+This is the second version.", diff)

        # Check that the initial version returns None for get_diff_to_previous
        self.assertIsNone(self.initial_version.get_diff_to_previous())


class SolutionFormTests(TestCase):
    """
    Tests for the SolutionForm.
    """

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="StrongPassword123"
        )

        # Create a test tag
        self.tag = Tag.objects.create(name="Test Tag")

    def test_solution_form_valid(self):
        """Test that the form is valid with correct data."""
        form_data = {
            "title": "Test Solution",
            "content": "# Test Content\n\nThis is a test solution.",
            "tags_input": "Test Tag, New Tag, Python, Django, API",
            "is_published": True,
            "change_comment": "Initial version",
        }
        form = SolutionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_solution_form_save(self):
        """Test that the form saves a solution and creates a version."""
        form_data = {
            "title": "Test Solution",
            "content": "# Test Content\n\nThis is a test solution.",
            "tags_input": "Test Tag, New Tag, Python, Django, API",
            "is_published": True,
            "change_comment": "Initial version",
        }
        form = SolutionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

        # Save the form
        solution = form.save()

        # Check that the solution was created correctly
        self.assertEqual(solution.title, "Test Solution")
        self.assertEqual(solution.content, "# Test Content\n\nThis is a test solution.")
        self.assertEqual(solution.author, self.user)
        self.assertTrue(solution.is_published)

        # Check that the tags were created and added
        self.assertEqual(solution.tags.count(), 5)  # Updated to expect 5 tags
        self.assertTrue(solution.tags.filter(name="Test Tag").exists())
        self.assertTrue(solution.tags.filter(name="New Tag").exists())
        self.assertTrue(solution.tags.filter(name="Python").exists())
        self.assertTrue(solution.tags.filter(name="Django").exists())
        self.assertTrue(solution.tags.filter(name="API").exists())

        # Check that a version was created
        self.assertEqual(solution.versions.count(), 1)
        version = solution.versions.first()
        self.assertEqual(version.content, "# Test Content\n\nThis is a test solution.")
        self.assertEqual(version.created_by, self.user)
        self.assertEqual(version.change_comment, "Initial version")
        self.assertEqual(version.version_number, 1)


class SolutionViewTests(TestCase):
    """
    Tests for the solution views.
    """

    def setUp(self):
        # Create a test client
        self.client = Client()

        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="test1@example.com",
            password="StrongPassword123",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="StrongPassword123",
        )

        # Create test tags
        self.tag1 = Tag.objects.create(name="Tag1")
        self.tag2 = Tag.objects.create(name="Tag2")

        # Create test solutions
        self.solution1 = Solution.objects.create(
            title="Solution 1",
            content="# Solution 1\n\nThis is solution 1.",
            author=self.user1,
            is_published=True,
        )
        self.solution1.tags.add(self.tag1)

        self.solution2 = Solution.objects.create(
            title="Solution 2",
            content="# Solution 2\n\nThis is solution 2.",
            author=self.user2,
            is_published=True,
        )
        self.solution2.tags.add(self.tag2)

        self.unpublished_solution = Solution.objects.create(
            title="Unpublished Solution",
            content="# Unpublished Solution\n\nThis is an unpublished solution.",
            author=self.user1,
            is_published=False,
        )

        # Create versions for the solutions
        SolutionVersion.objects.create(
            solution=self.solution1,
            content=self.solution1.content,
            created_by=self.user1,
            change_comment="Initial version",
        )

        SolutionVersion.objects.create(
            solution=self.solution2,
            content=self.solution2.content,
            created_by=self.user2,
            change_comment="Initial version",
        )

        SolutionVersion.objects.create(
            solution=self.unpublished_solution,
            content=self.unpublished_solution.content,
            created_by=self.user1,
            change_comment="Initial version",
        )

    def test_solution_list_view(self):
        """Test that the solution list view shows published solutions."""
        response = self.client.get(reverse("solutions:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solution 1")
        self.assertContains(response, "Solution 2")
        self.assertNotContains(response, "Unpublished Solution")

    def test_solution_list_view_with_tag_filter(self):
        """Test that the solution list view can filter by tag."""
        response = self.client.get(reverse("solutions:list") + f"?tag={self.tag1.slug}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solution 1")
        self.assertNotContains(response, "Solution 2")

    def test_solution_detail_view(self):
        """Test that the solution detail view shows a solution."""
        response = self.client.get(
            reverse("solutions:detail", kwargs={"slug": self.solution1.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solution 1")
        self.assertContains(response, '<h1 id="solution-1">Solution 1</h1>')

    def test_solution_detail_view_unpublished(self):
        """Test that unpublished solutions are only visible to the author."""
        # Anonymous user should get a 403
        response = self.client.get(
            reverse("solutions:detail", kwargs={"slug": self.unpublished_solution.slug})
        )
        self.assertEqual(response.status_code, 403)

        # Non-author user should get a 403
        self.client.login(username="testuser2", password="StrongPassword123")
        response = self.client.get(
            reverse("solutions:detail", kwargs={"slug": self.unpublished_solution.slug})
        )
        self.assertEqual(response.status_code, 403)

        # Author should be able to view the solution
        self.client.login(username="testuser1", password="StrongPassword123")
        response = self.client.get(
            reverse("solutions:detail", kwargs={"slug": self.unpublished_solution.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unpublished Solution")

    def test_solution_create_view(self):
        """Test that the solution create view creates a solution."""
        # Login required
        response = self.client.get(reverse("solutions:create"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Login and create a solution
        self.client.login(username="testuser1", password="StrongPassword123")
        response = self.client.get(reverse("solutions:create"))
        self.assertEqual(response.status_code, 200)

        form_data = {
            "title": "New Solution",
            "content": "# New Solution\n\nThis is a new solution.",
            "tags_input": "Tag1, New Tag, Python, Django, API",
            "is_published": True,
            "change_comment": "Initial version",
        }
        response = self.client.post(reverse("solutions:create"), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect to detail

        # Check that the solution was created
        solution = Solution.objects.get(title="New Solution")
        self.assertEqual(solution.content, "# New Solution\n\nThis is a new solution.")
        self.assertEqual(solution.author, self.user1)
        self.assertTrue(solution.is_published)

        # Check that the tags were added
        self.assertEqual(solution.tags.count(), 5)
        self.assertTrue(solution.tags.filter(name="Tag1").exists())
        self.assertTrue(solution.tags.filter(name="New Tag").exists())
        self.assertTrue(solution.tags.filter(name="Python").exists())
        self.assertTrue(solution.tags.filter(name="Django").exists())
        self.assertTrue(solution.tags.filter(name="API").exists())

        # Check that a version was created
        self.assertEqual(solution.versions.count(), 1)
        version = solution.versions.first()
        self.assertEqual(version.content, "# New Solution\n\nThis is a new solution.")
        self.assertEqual(version.created_by, self.user1)
        self.assertEqual(version.change_comment, "Initial version")
        self.assertEqual(version.version_number, 1)
