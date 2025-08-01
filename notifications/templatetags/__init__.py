from django import template
from django.db.models import Q

register = template.Library()

@register.simple_tag
def unread_notifications_count(user):
    """Return the count of unread notifications for a user."""
    if user.is_authenticated:
        return user.notifications.filter(is_read=False).count()
    return 0
