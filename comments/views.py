from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect

from notifications.utils import create_notification
from solutions.models import Solution

from .forms import CommentForm, ReplyForm
from .models import Comment


@login_required
def add_comment(request, slug):
    """Add a new comment to a solution."""
    solution = get_object_or_404(Solution, slug=slug)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.solution = solution
            comment.author = request.user
            comment.save()

            # Create notification for the solution author
            if solution.author != request.user:
                create_notification(
                    recipient=solution.author,
                    actor=request.user,
                    verb="commented on your solution",
                    content_object=comment,
                    description=f"New comment on '{solution.title}'",
                )

            messages.success(request, "Your comment was added successfully.")
            return redirect("solutions:detail", slug=slug)
    else:
        form = CommentForm()

    return redirect("solutions:detail", slug=slug)


@login_required
def add_reply(request, slug, comment_id):
    """Add a reply to an existing comment."""
    solution = get_object_or_404(Solution, slug=slug)
    parent_comment = get_object_or_404(Comment, id=comment_id, solution=solution)

    if request.method == "POST":
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.solution = solution
            reply.author = request.user
            reply.parent = parent_comment
            reply.save()

            # Create notification for the parent comment author
            if parent_comment.author != request.user:
                create_notification(
                    recipient=parent_comment.author,
                    actor=request.user,
                    verb="replied to your comment",
                    content_object=reply,
                    description=f"New reply to your comment on '{solution.title}'",
                )

            messages.success(request, "Your reply was added successfully.")

    return redirect("solutions:detail", slug=slug)


@login_required
def delete_comment(request, comment_id):
    """Delete a comment."""
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    solution_slug = comment.solution.slug

    if request.method == "POST":
        comment.delete()
        messages.success(request, "Your comment was deleted successfully.")

        # If AJAX request, return JSON response
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"status": "success"})

    return redirect("solutions:detail", slug=solution_slug)
