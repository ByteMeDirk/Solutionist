from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.core.paginator import Paginator

from .models import Tag
from solutions.models import Solution


def tag_list(request):
    """
    View to list all tags with their usage statistics.
    """
    # Get all tags with solution count and average rating
    tags = Tag.objects.annotate(
        solution_count=Count('solutions', distinct=True),
        avg_rating=Avg('solutions__ratings__value')
    ).order_by('-solution_count')

    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        tags = tags.filter(name__icontains=search_query)

    # Sorting
    sort_by = request.GET.get('sort', '-solutions')
    if sort_by == 'name':
        tags = tags.order_by('name')
    elif sort_by == '-name':
        tags = tags.order_by('-name')
    elif sort_by == 'solutions':
        tags = tags.order_by('solution_count', 'name')
    elif sort_by == '-solutions':
        tags = tags.order_by('-solution_count', 'name')

    # Paginate
    paginator = Paginator(tags, 30)  # 30 tags per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_tags': Tag.objects.count(),
        'total_solutions': Solution.objects.filter(is_published=True).count(),
    }

    return render(request, 'tags/tag_list.html', context)


def tag_detail(request, slug):
    """
    View to show details of a specific tag and its solutions.
    """
    tag = get_object_or_404(Tag, slug=slug)

    # Get solutions with this tag
    solutions = Solution.objects.filter(
        tags=tag,
        is_published=True
    ).select_related('author').prefetch_related('tags')

    # Calculate statistics
    total_solutions = solutions.count()
    total_authors = solutions.values('author').distinct().count()
    avg_rating = solutions.filter(ratings__isnull=False).aggregate(
        avg=Avg('ratings__value')
    )['avg'] or 0

    # Sort solutions
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'title':
        solutions = solutions.order_by('title')
    elif sort_by == '-title':
        solutions = solutions.order_by('-title')
    elif sort_by == 'rating':
        solutions = solutions.annotate(avg_rating=Avg('ratings__value')).order_by('avg_rating', '-created_at')
    elif sort_by == '-rating':
        solutions = solutions.annotate(avg_rating=Avg('ratings__value')).order_by('-avg_rating', '-created_at')
    else:  # default to most recent
        solutions = solutions.order_by('-created_at')

    # Paginate solutions
    paginator = Paginator(solutions, 10)  # 10 solutions per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get related tags
    related_tags = Tag.objects.filter(
        solutions__in=solutions
    ).annotate(
        solution_count=Count('solutions')
    ).exclude(id=tag.id).order_by('-solution_count')[:10]

    context = {
        'tag': tag,
        'page_obj': page_obj,
        'sort_by': sort_by,
        'total_solutions': total_solutions,
        'total_authors': total_authors,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'related_tags': related_tags,
    }

    return render(request, 'tags/tag_detail.html', context)


def tag_autocomplete(request):
    """
    View for tag autocomplete functionality.
    """
    query = request.GET.get('q', '')
    if query:
        tags = Tag.objects.filter(name__icontains=query).values('name')[:10]
        return JsonResponse(list(tags), safe=False)
    return JsonResponse([], safe=False)
