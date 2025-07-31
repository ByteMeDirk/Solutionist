from django.urls import path
from . import views

app_name = 'solutions'

urlpatterns = [
    # List and search solutions
    path('', views.solution_list, name='list'),
    
    # Create solution
    path('create/', views.solution_create, name='create'),
    
    # Solution detail, edit, delete
    path('<slug:slug>/', views.solution_detail, name='detail'),
    path('<slug:slug>/edit/', views.solution_edit, name='edit'),
    path('<slug:slug>/delete/', views.solution_delete, name='delete'),
    
    # Version history and comparison
    path('<slug:slug>/history/', views.solution_history, name='history'),
    path('<slug:slug>/version/<int:version_number>/', views.solution_version, name='version'),
    path('<slug:slug>/compare/', views.solution_compare, name='compare'),
]