from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages

from .models import Solution
from .ratings import Rating
from .forms import RatingForm


@login_required
def rate_solution(request, slug):
    """Allow users to rate a solution."""
    solution = get_object_or_404(Solution, slug=slug)

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            try:
                # Update existing rating or create new one
                try:
                    rating = Rating.objects.get(solution=solution, user=request.user)
                    rating.value = form.cleaned_data['value']
                    rating.save()
                    message = "Your rating has been updated."
                except Rating.DoesNotExist:
                    rating = form.save(commit=False)
                    rating.solution = solution
                    rating.user = request.user
                    rating.save()
                    message = "Thank you for rating this solution!"

                messages.success(request, message)

                # If AJAX request, return JSON response with updated rating data
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'average_rating': solution.get_average_rating(),
                        'rating_count': solution.get_rating_count(),
                        'user_rating': rating.value,
                        'message': message
                    })

            except Exception as e:
                # Handle any unexpected errors
                error_message = f"Error processing rating: {str(e)}"
                messages.error(request, error_message)

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_message
                    }, status=400)
        else:
            # Form validation failed
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': "Invalid rating submitted."
                }, status=400)
            messages.error(request, "Invalid rating submitted.")

    return redirect('solutions:detail', slug=slug)


@login_required
def delete_rating(request, slug):
    """Allow users to remove their rating."""
    solution = get_object_or_404(Solution, slug=slug)

    if request.method == 'POST':
        try:
            rating = Rating.objects.get(solution=solution, user=request.user)
            rating.delete()
            messages.success(request, "Your rating has been removed.")

            # If AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'average_rating': solution.get_average_rating(),
                    'rating_count': solution.get_rating_count()
                })
        except Rating.DoesNotExist:
            messages.warning(request, "You haven't rated this solution yet.")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': "You haven't rated this solution yet."
                }, status=400)
        except Exception as e:
            # Handle any unexpected errors
            error_message = f"Error removing rating: {str(e)}"
            messages.error(request, error_message)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_message
                }, status=400)

    return redirect('solutions:detail', slug=slug)
