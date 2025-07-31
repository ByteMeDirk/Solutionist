from django.db import models
from django.conf import settings
from django.utils.html import mark_safe
from solutions.models import Solution
import markdown


class Comment(models.Model):
    """
    Model for storing comments on solutions.
    """
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    content_html = models.TextField(editable=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def __str__(self):
        return f'Comment by {self.author.username} on {self.solution.title}'

    def save(self, *args, **kwargs):
        # Convert markdown to HTML
        self.content_html = markdown.markdown(
            self.content,
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.codehilite',
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',
            ]
        )
        super().save(*args, **kwargs)

    def get_content_html(self):
        """Return the HTML content, marked as safe."""
        return mark_safe(self.content_html)
