from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q

from .models import Notification


@login_required
def notification_list(request):
    """Display a list of the user's notifications."""
    notifications = request.user.notifications.all()
    unread_count = notifications.filter(is_read=False).count()

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def notification_mark_as_read(request, notification_id):
    """Mark a specific notification as read."""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    notification.mark_as_read()

    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    # Otherwise redirect to the notification's target
    return redirect(notification.get_absolute_url())


@login_required
def notification_mark_all_as_read(request):
    """Mark all notifications as read."""
    request.user.notifications.filter(is_read=False).update(is_read=True)

    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:list')


@login_required
def notification_delete(request, notification_id):
    """Delete a specific notification."""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    notification.delete()

    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    messages.success(request, 'Notification deleted.')
    return redirect('notifications:list')


@login_required
def notification_delete_all(request):
    """Delete all notifications."""
    request.user.notifications.all().delete()

    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    messages.success(request, 'All notifications deleted.')
    return redirect('notifications:list')


@login_required
def get_unread_count(request):
    """Return the number of unread notifications for the current user."""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})
