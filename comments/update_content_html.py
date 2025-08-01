import os
import sys

import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solutionist.settings")
django.setup()

import markdown

from comments.models import Comment


def update_comments_html():
    """Update all comments to add HTML content."""
    comments = Comment.objects.all()
    count = 0

    for comment in comments:
        old_content_html = (
            comment.content_html if hasattr(comment, "content_html") else None
        )

        # Convert markdown to HTML
        comment.content_html = markdown.markdown(
            comment.content,
            extensions=[
                "markdown.extensions.fenced_code",
                "markdown.extensions.codehilite",
                "markdown.extensions.tables",
                "markdown.extensions.nl2br",
            ],
        )

        if old_content_html != comment.content_html:
            comment.save(update_fields=["content_html"])
            count += 1

    return count


if __name__ == "__main__":
    print("Updating comment HTML content...")
    count = update_comments_html()
    print(f"Updated {count} comments with HTML content.")
