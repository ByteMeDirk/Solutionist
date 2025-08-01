from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse


class Notification(models.Model):
    """
    Model for storing user notifications about comments and replies.
    """

    # The user who will receive the notification
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )

    # The user who performed the action
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="actions"
    )

    # Generic foreign key to the object that the notification is about
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    # Notification details
    verb = models.CharField(max_length=255)  # e.g., "commented on", "replied to"
    description = models.TextField(blank=True)

    # Notification status
    is_read = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "created_at"]),
        ]

    def __str__(self):
        return f"{self.actor} {self.verb} - {self.created_at}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()

    def get_absolute_url(self):
        """Return the URL to redirect to when a notification is clicked."""
        if self.content_type.model == "comment":
            comment = self.content_object
            solution = comment.solution
            return f"{reverse('solutions:detail', kwargs={'slug': solution.slug})}#comment-{comment.id}"
        return "/"

    @classmethod
    def unread_count(cls, user):
        """Return the count of unread notifications for a user."""
        if user.is_authenticated:
            return cls.objects.filter(recipient=user, is_read=False).count()
        return 0
