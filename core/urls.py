from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("docs/mcp/", views.mcp_documentation, name="mcp_docs"),
]
