from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.http import HttpResponseForbidden
from django.utils.safestring import mark_safe
import difflib
import markdown

from .models import Solution, SolutionVersion
from .forms import SolutionForm, SolutionVersionCompareForm, SolutionSearchForm
from tags.models import Tag


def solution_list(request):
    """
    View for listing all published solutions with enhanced search functionality.
    """
    # Initialize the search form
    search_form = SolutionSearchForm(request.GET or None)

    # Start with all published solutions
    solutions = Solution.objects.filter(is_published=True)
    
    # Apply filters based on form data
    if search_form.is_valid():
        # Apply text search filter
        query = search_form.cleaned_data.get('query')
        if query:
            solutions = solutions.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(author__username__icontains=query)
            ).distinct()

        # Apply tag filters
        tags_input = search_form.cleaned_data.get('tags')
        if tags_input:
            # Split comma-separated tags
            tag_names = [t.strip() for t in tags_input.split(',') if t.strip()]

            # Filter by each tag
            for tag_name in tag_names:
                solutions = solutions.filter(tags__name__icontains=tag_name)

        # Apply sorting
        sort_by = search_form.cleaned_data.get('sort_by')
        if sort_by:
            if sort_by == 'date_desc':
                solutions = solutions.order_by('-created_at')
            elif sort_by == 'date_asc':
                solutions = solutions.order_by('created_at')
            elif sort_by == 'rating_desc':
                solutions = solutions.annotate(avg_rating=Avg('ratings__value')).order_by('-avg_rating')
            elif sort_by == 'views_desc':
                solutions = solutions.order_by('-view_count')
    else:
        # Default sort by most recently updated
        solutions = solutions.order_by('-updated_at')

    # Paginate results
    paginator = Paginator(solutions, 10)  # 10 solutions per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get popular tags
    popular_tags = Tag.objects.annotate(solution_count=Count('solutions')).order_by('-solution_count')[:10]

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'popular_tags': popular_tags
    }
    
    return render(request, 'solutions/solution_list.html', context)


def solution_detail(request, slug):
    """
    View for displaying a solution with comments and ratings.
    """
    solution = get_object_or_404(Solution, slug=slug)
    
    # If solution is not published, only the author can view it
    if not solution.is_published and (not request.user.is_authenticated or request.user != solution.author):
        return HttpResponseForbidden("You don't have permission to view this solution.")
    
    # Increment view count (only for published solutions)
    if solution.is_published:
        solution.increment_view_count()
    
    # Get related solutions based on tags
    related_solutions = Solution.objects.filter(
        is_published=True,
        tags__in=solution.tags.all()
    ).exclude(id=solution.id).distinct()[:5]
    
    # Get top-level comments (no parent)
    comments = solution.comments.filter(parent=None, is_active=True)

    # Comment form
    from comments.forms import CommentForm, ReplyForm
    comment_form = CommentForm()
    reply_form = ReplyForm()

    # Rating form
    from .forms import RatingForm
    rating_form = RatingForm()
    user_rating = None

    if request.user.is_authenticated:
        user_rating = solution.get_user_rating(request.user)
        if user_rating:
            rating_form.initial = {'value': user_rating}

    context = {
        'solution': solution,
        'related_solutions': related_solutions,
        'comments': comments,
        'comment_form': comment_form,
        'reply_form': reply_form,
        'rating_form': rating_form,
        'user_rating': user_rating
    }
    
    return render(request, 'solutions/solution_detail.html', context)


@login_required
def solution_create(request):
    """
    View for creating a new solution.
    """
    if request.method == 'POST':
        form = SolutionForm(request.POST, user=request.user)
        if form.is_valid():
            solution = form.save()
            messages.success(request, 'Solution created successfully!')
            return redirect('solutions:detail', slug=solution.slug)
    else:
        form = SolutionForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create Solution',
    }
    
    return render(request, 'solutions/solution_form.html', context)


@login_required
def solution_edit(request, slug):
    """
    View for editing an existing solution.
    """
    solution = get_object_or_404(Solution, slug=slug)
    
    # Only the author can edit the solution
    if request.user != solution.author:
        return HttpResponseForbidden("You don't have permission to edit this solution.")
    
    if request.method == 'POST':
        form = SolutionForm(request.POST, instance=solution, user=request.user)
        if form.is_valid():
            solution = form.save()
            messages.success(request, 'Solution updated successfully!')
            return redirect('solutions:detail', slug=solution.slug)
    else:
        form = SolutionForm(instance=solution, user=request.user)
    
    context = {
        'form': form,
        'solution': solution,
        'title': 'Edit Solution',
    }
    
    return render(request, 'solutions/solution_form.html', context)


@login_required
def solution_delete(request, slug):
    """
    View for deleting a solution.
    """
    solution = get_object_or_404(Solution, slug=slug)
    
    # Only the author can delete the solution
    if request.user != solution.author:
        return HttpResponseForbidden("You don't have permission to delete this solution.")
    
    if request.method == 'POST':
        solution.delete()
        messages.success(request, 'Solution deleted successfully!')
        return redirect('solutions:list')
    
    context = {
        'solution': solution,
    }
    
    return render(request, 'solutions/solution_confirm_delete.html', context)


def solution_history(request, slug):
    """
    View for displaying the version history of a solution.
    """
    solution = get_object_or_404(Solution, slug=slug)
    
    # If solution is not published, only the author can view its history
    if not solution.is_published and (not request.user.is_authenticated or request.user != solution.author):
        return HttpResponseForbidden("You don't have permission to view this solution's history.")
    
    versions = solution.versions.all().order_by('-version_number')
    
    context = {
        'solution': solution,
        'versions': versions,
    }
    
    return render(request, 'solutions/solution_history.html', context)


def solution_version(request, slug, version_number):
    """
    View for displaying a specific version of a solution.
    """
    solution = get_object_or_404(Solution, slug=slug)
    
    # If solution is not published, only the author can view its versions
    if not solution.is_published and (not request.user.is_authenticated or request.user != solution.author):
        return HttpResponseForbidden("You don't have permission to view this solution's versions.")
    
    version = get_object_or_404(SolutionVersion, solution=solution, version_number=version_number)
    latest_version = solution.get_latest_version()
    
    # Render the markdown content to HTML
    version_html = markdown.markdown(
        version.content,
        extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.tables',
            'markdown.extensions.toc',
        ]
    )
    
    context = {
        'solution': solution,
        'version': version,
        'latest_version': latest_version,
        'version_html': version_html,
    }
    
    return render(request, 'solutions/solution_version.html', context)


def solution_compare(request, slug):
    """
    View for comparing two versions of a solution.
    """
    solution = get_object_or_404(Solution, slug=slug)
    
    # If solution is not published, only the author can compare its versions
    if not solution.is_published and (not request.user.is_authenticated or request.user != solution.author):
        return HttpResponseForbidden("You don't have permission to compare this solution's versions.")
    
    version_a = None
    version_b = None
    diff_html = None
    
    if request.method == 'POST':
        form = SolutionVersionCompareForm(solution, request.POST)
        if form.is_valid():
            version_a = form.cleaned_data['version_a']
            version_b = form.cleaned_data['version_b']
    else:
        form = SolutionVersionCompareForm(solution)
        # Check if version_a and version_b are provided in GET parameters
        version_a_id = request.GET.get('version_a')
        version_b_id = request.GET.get('version_b')
        if version_a_id and version_b_id:
            try:
                version_a = SolutionVersion.objects.get(pk=version_a_id, solution=solution)
                version_b = SolutionVersion.objects.get(pk=version_b_id, solution=solution)
                form.fields['version_a'].initial = version_a.pk
                form.fields['version_b'].initial = version_b.pk
            except SolutionVersion.DoesNotExist:
                pass
    
    # Generate diff if both versions are selected
    if version_a and version_b:
        diff_html = generate_diff_html(version_a.content, version_b.content)
    
    context = {
        'solution': solution,
        'form': form,
        'version_a': version_a,
        'version_b': version_b,
        'diff_html': mark_safe(diff_html) if diff_html else None,
    }
    
    return render(request, 'solutions/solution_compare.html', context)


def generate_diff_html(text_a, text_b):
    """
    Generate HTML diff between two texts with custom styling.
    """
    # Create a HtmlDiff object with custom settings
    diff = difflib.HtmlDiff(tabsize=4)
    
    # Generate the diff table
    diff_table = diff.make_table(
        text_a.splitlines(),
        text_b.splitlines(),
        fromdesc='Previous Version',
        todesc='Current Version',
        context=True,
        numlines=3
    )
    
    # Apply custom styling to the diff table
    # Replace the default styles with our custom Bootstrap-compatible styles
    diff_table = diff_table.replace(
        '<table class="diff" id="difflib_chg_to0__top"',
        '<table class="diff-table table table-sm"'
    )
    
    # Replace the default colors with our custom colors
    diff_table = diff_table.replace('background-color: #ffdddd;', 'background-color: #f8d7da;')  # Removed lines
    diff_table = diff_table.replace('background-color: #ddffdd;', 'background-color: #d4edda;')  # Added lines
    diff_table = diff_table.replace('background-color: #e0e0e0;', 'background-color: #e2e3e5;')  # Info lines
    
    # Add classes to cells for easier styling
    diff_table = diff_table.replace('<td class="diff_header"', '<td class="diff-line-num"')
    
    # Remove the legend and other unnecessary elements
    diff_table = diff_table.split('<table class="diff" summary="Legends">')[0]
    
    return diff_table
