from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path(
        "<int:notification_id>/mark-as-read/",
        views.notification_mark_as_read,
        name="mark_as_read",
    ),
    path(
        "mark-all-as-read/",
        views.notification_mark_all_as_read,
        name="mark_all_as_read",
    ),
    path("<int:notification_id>/delete/", views.notification_delete, name="delete"),
    path("delete-all/", views.notification_delete_all, name="delete_all"),
    path("unread-count/", views.get_unread_count, name="unread_count"),
]
