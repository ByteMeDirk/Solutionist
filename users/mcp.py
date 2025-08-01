import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_token():
    """Generate a secure random token for MCP authentication"""
    return secrets.token_urlsafe(32)


class MCPToken(models.Model):
    """
    Model for storing MCP (Model Context Protocol) tokens for users.
    These tokens allow users to read and write solutions via API integrations.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mcp_tokens"
    )
    token = models.CharField(max_length=64, default=generate_token, unique=True)
    name = models.CharField(
        max_length=100, help_text="A name to help you identify this token"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "MCP Token"
        verbose_name_plural = "MCP Tokens"

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def save(self, *args, **kwargs):
        # Set default expiration if not provided (1 year from creation)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=365)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if the token is valid (active and not expired)"""
        return self.is_active and (
            self.expires_at is None or self.expires_at > timezone.now()
        )

    def update_last_used(self):
        """Update the last_used timestamp to current time"""
        self.last_used = timezone.now()
        self.save(update_fields=["last_used"])

    def revoke(self):
        """Revoke this token"""
        self.is_active = False
        self.save(update_fields=["is_active"])
