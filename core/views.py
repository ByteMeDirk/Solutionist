from django.shortcuts import render


def home(request):
    """
    View function for the home page.
    """
    return render(request, "home.html")


def handler404(request, exception):
    """
    Custom 404 error handler.
    """
    return render(request, "errors/404.html", status=404)


def handler500(request):
    """
    Custom 500 error handler.
    """
    return render(request, "errors/500.html", status=500)
