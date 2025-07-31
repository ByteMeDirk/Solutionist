from django.shortcuts import render
from solutions.models import Solution


def home(request):
    """
    View function for the home page.
    """
    # Get recent published solutions
    recent_solutions = Solution.objects.filter(is_published=True).order_by('-created_at')[:5]
    
    context = {
        'recent_solutions': recent_solutions,
    }
    
    return render(request, "home.html", context)


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
