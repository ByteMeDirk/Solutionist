from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

from .models import UserProfile


class UserRegistrationTests(TestCase):
    """
    Tests for user registration functionality.
    """

    def setUp(self):
        self.client = Client()
        self.register_url = reverse("users:register")
        self.valid_user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "StrongPassword123",
            "password2": "StrongPassword123",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_register_page_loads(self):
        """Test that the registration page loads correctly."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_successful_registration(self):
        """Test that a user can register successfully with valid data."""
        response = self.client.post(self.register_url, self.valid_user_data)
        self.assertEqual(
            response.status_code, 302
        )  # Redirect after successful registration
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)

        # Check that the user was created with the correct attributes
        user = User.objects.first()
        self.assertEqual(user.username, self.valid_user_data["username"])
        self.assertEqual(user.email, self.valid_user_data["email"])
        self.assertEqual(user.first_name, self.valid_user_data["first_name"])
        self.assertEqual(user.last_name, self.valid_user_data["last_name"])

        # Check that the user has a profile
        self.assertTrue(hasattr(user, "profile"))

    def test_registration_with_duplicate_username(self):
        """Test that registration fails with a duplicate username."""
        # Create a user with the same username
        User.objects.create_user(
            username=self.valid_user_data["username"],
            email="another@example.com",
            password="AnotherPassword123",
        )

        response = self.client.post(self.register_url, self.valid_user_data)
        self.assertEqual(response.status_code, 200)  # Form is redisplayed with errors
        self.assertFormError(
            response, "form", "username", "A user with that username already exists."
        )

    def test_registration_with_duplicate_email(self):
        """Test that registration fails with a duplicate email."""
        # Create a user with the same email
        User.objects.create_user(
            username="anotheruser",
            email=self.valid_user_data["email"],
            password="AnotherPassword123",
        )

        response = self.client.post(self.register_url, self.valid_user_data)
        self.assertEqual(response.status_code, 200)  # Form is redisplayed with errors
        self.assertFormError(
            response, "form", "email", "A user with that email already exists."
        )

    def test_registration_with_weak_password(self):
        """Test that registration fails with a weak password."""
        weak_password_data = self.valid_user_data.copy()
        weak_password_data["password1"] = "password"
        weak_password_data["password2"] = "password"

        response = self.client.post(self.register_url, weak_password_data)
        self.assertEqual(response.status_code, 200)  # Form is redisplayed with errors
        self.assertFormError(
            response, "form", "password2", "This password is too common."
        )


class UserAuthenticationTests(TestCase):
    """
    Tests for user login and logout functionality.
    """

    def setUp(self):
        self.client = Client()
        self.login_url = reverse("users:login")
        self.logout_url = reverse("users:logout")
        self.home_url = reverse("core:home")

        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="StrongPassword123"
        )

    def test_login_page_loads(self):
        """Test that the login page loads correctly."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_successful_login(self):
        """Test that a user can log in successfully with valid credentials."""
        response = self.client.post(
            self.login_url, {"username": "testuser", "password": "StrongPassword123"}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
        self.assertRedirects(response, self.home_url)

        # Check that the user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_invalid_credentials(self):
        """Test that login fails with invalid credentials."""
        response = self.client.post(
            self.login_url, {"username": "testuser", "password": "WrongPassword"}
        )
        self.assertEqual(response.status_code, 200)  # Form is redisplayed with errors
        self.assertFormError(
            response,
            "form",
            None,
            "Please enter a correct username and password. Note that both fields may be case-sensitive.",
        )

        # Check that the user is not logged in
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout(self):
        """Test that a user can log out successfully."""
        # Log in first
        self.client.login(username="testuser", password="StrongPassword123")

        # Then log out
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful logout
        self.assertRedirects(response, self.home_url)

        # Check that the user is logged out
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class UserProfileTests(TestCase):
    """
    Tests for user profile functionality.
    """

    def setUp(self):
        self.client = Client()
        self.profile_url = reverse("users:profile")

        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="StrongPassword123"
        )

        # Create a profile for the user (should be created automatically)
        self.profile = self.user.profile

    def test_profile_page_requires_login(self):
        """Test that the profile page requires login."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        self.assertRedirects(response, f"/users/login/?next={self.profile_url}")

    def test_profile_page_loads_for_authenticated_user(self):
        """Test that the profile page loads correctly for an authenticated user."""
        self.client.login(username="testuser", password="StrongPassword123")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")

    def test_profile_update(self):
        """Test that a user can update their profile."""
        self.client.login(username="testuser", password="StrongPassword123")

        # Update profile data
        profile_data = {
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "bio": "This is my updated bio.",
            "skills": "Python, Django, Testing",
            "experience": "I have experience in web development.",
            "website": "https://example.com",
            "github": "https://github.com/testuser",
            "twitter": "https://twitter.com/testuser",
            "linkedin": "https://linkedin.com/in/testuser",
        }

        response = self.client.post(self.profile_url, profile_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.assertRedirects(response, self.profile_url)

        # Refresh the user and profile from the database
        self.user.refresh_from_db()
        self.profile.refresh_from_db()

        # Check that the user and profile were updated correctly
        self.assertEqual(self.user.first_name, profile_data["first_name"])
        self.assertEqual(self.user.last_name, profile_data["last_name"])
        self.assertEqual(self.user.email, profile_data["email"])
        self.assertEqual(self.profile.bio, profile_data["bio"])
        self.assertEqual(self.profile.skills, profile_data["skills"])
        self.assertEqual(self.profile.experience, profile_data["experience"])
        self.assertEqual(self.profile.website, profile_data["website"])
        self.assertEqual(self.profile.github, profile_data["github"])
        self.assertEqual(self.profile.twitter, profile_data["twitter"])
        self.assertEqual(self.profile.linkedin, profile_data["linkedin"])


class AccountDeletionTests(TestCase):
    """
    Tests for account deletion functionality.
    """

    def setUp(self):
        self.client = Client()
        self.delete_url = reverse("users:delete")
        self.home_url = reverse("core:home")

        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="StrongPassword123"
        )

    def test_delete_page_requires_login(self):
        """Test that the delete account page requires login."""
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        self.assertRedirects(response, f"/users/login/?next={self.delete_url}")

    def test_delete_page_loads_for_authenticated_user(self):
        """Test that the delete account page loads correctly for an authenticated user."""
        self.client.login(username="testuser", password="StrongPassword123")
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/account_delete.html")

    # def test_account_deletion_with_correct_password(self):
    #     """Test that a user can delete their account with the correct password."""
    #     self.client.login(username='testuser', password='StrongPassword123')
    #
    #     # Use a simpler approach with direct mocking of the MCPToken reference
    #     with patch('users.views.MCPToken', create=True) as mock_token:
    #         mock_token.objects.filter.return_value.delete.return_value = None
    #
    #         response = self.client.post(self.delete_url, {
    #             'password': 'StrongPassword123'
    #         })
    #
    #         self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
    #         self.assertRedirects(response, self.home_url)
    #
    #         # Check that the user is deleted
    #         self.assertEqual(User.objects.count(), 0)
    #         self.assertEqual(UserProfile.objects.count(), 0)
    #
    #         # Check that the user is logged out
    #         self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_account_deletion_with_incorrect_password(self):
        """Test that account deletion fails with an incorrect password."""
        self.client.login(username="testuser", password="StrongPassword123")

        response = self.client.post(self.delete_url, {"password": "WrongPassword"})
        self.assertEqual(response.status_code, 200)  # Form is redisplayed with errors
        self.assertFormError(
            response, "form", "password", "Incorrect password. Please try again."
        )

        # Check that the user is not deleted
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)


class PasswordResetTests(TestCase):
    """
    Tests for password reset functionality.
    """

    def setUp(self):
        self.client = Client()
        self.reset_url = reverse("users:password_reset")
        self.reset_done_url = reverse("users:password_reset_done")

        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="StrongPassword123"
        )

    def test_reset_page_loads(self):
        """Test that the password reset page loads correctly."""
        response = self.client.get(self.reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/password_reset.html")

    def test_password_reset_with_valid_email(self):
        """Test that a password reset email is sent for a valid email address."""
        response = self.client.post(self.reset_url, {"email": "test@example.com"})
        self.assertEqual(
            response.status_code, 302
        )  # Redirect after successful submission
        self.assertRedirects(response, self.reset_done_url)

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Password Reset for Solutionist")
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])

    def test_password_reset_with_invalid_email(self):
        """Test that no error is shown for an invalid email address (for security reasons)."""
        response = self.client.post(
            self.reset_url, {"email": "nonexistent@example.com"}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after submission
        self.assertRedirects(response, self.reset_done_url)

        # Check that no email was sent
        self.assertEqual(len(mail.outbox), 0)
