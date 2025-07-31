from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    path('add/<slug:slug>/', views.add_comment, name='add_comment'),
    path('reply/<slug:slug>/<int:comment_id>/', views.add_reply, name='add_reply'),
    path('delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
]
