from django.contrib.contenttypes.models import ContentType

from .models import Notification


def create_notification(recipient, actor, verb, content_object, description=""):
    """
    Create a new notification.

    Args:
        recipient: User who will receive the notification
        actor: User who performed the action
        verb: String describing the action (e.g., "commented on your solution")
        content_object: The object the notification is about (e.g., Comment)
        description: Optional additional text
    """
    if recipient == actor:
        # Don't notify users about their own actions
        return None

    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=verb,
        content_type=ContentType.objects.get_for_model(content_object),
        object_id=content_object.id,
        description=description,
    )

    return notification
