from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Count
from solutions.models import Solution


def home(request):
    """
    View function for the home page with live statistics.
    """
    # Get recent published solutions
    recent_solutions = Solution.objects.filter(is_published=True).order_by('-created_at')[:5]
    
    # Calculate statistics
    solution_count = Solution.objects.filter(is_published=True).count()
    user_count = get_user_model().objects.filter(is_active=True).count()
    language_count = Solution.objects.filter(is_published=True).values('tags__name').distinct().count()

    context = {
        'recent_solutions': recent_solutions,
        'stats': {
            'solution_count': solution_count,
            'user_count': user_count,
            'language_count': language_count,
        }
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
