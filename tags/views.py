from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count
from django.core.paginator import Paginator

from .models import Tag
from solutions.models import Solution


def tag_list(request):
    """
    View to list all tags with their solution count.
    """
    tags = Tag.objects.annotate(solution_count=Count('solutions')).order_by('-solution_count')

    # Paginate
    paginator = Paginator(tags, 30)  # 30 tags per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'tags/tag_list.html', context)


def tag_detail(request, slug):
    """
    View to display all solutions with a specific tag.
    """
    tag = get_object_or_404(Tag, slug=slug)
    solutions = Solution.objects.filter(tags=tag, is_published=True).order_by('-updated_at')

    # Paginate
    paginator = Paginator(solutions, 10)  # 10 solutions per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'tag': tag,
        'page_obj': page_obj,
    }

    return render(request, 'tags/tag_detail.html', context)


def tag_autocomplete(request):
    """
    View for tag autocomplete functionality.
    Returns JSON response with matching tags.
    """
    query = request.GET.get('q', '')
    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    tags = Tag.objects.filter(name__icontains=query).order_by('name')[:10]
    results = [{'id': tag.id, 'text': tag.name} for tag in tags]

    return JsonResponse({'results': results})
