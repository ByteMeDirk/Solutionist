from notifications.models import Notification

def notifications_processor(request):
    """
    Context processor that adds unread notification count to the template context.
    """
    context = {
        'unread_notifications_count': 0
    }

    if request.user.is_authenticated:
        context['unread_notifications_count'] = Notification.unread_count(request.user)

    return context
