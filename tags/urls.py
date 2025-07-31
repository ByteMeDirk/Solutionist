from django.urls import path
from . import views

app_name = 'tags'

urlpatterns = [
    path('', views.tag_list, name='list'),
    path('<slug:slug>/', views.tag_detail, name='detail'),
    path('autocomplete/', views.tag_autocomplete, name='autocomplete'),
]
