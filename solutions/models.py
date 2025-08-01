from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.db.models import Avg
import markdown
import difflib
import uuid

from tags.models import Tag
from .ai_services import generate_summary


class Solution(models.Model):
    """
    Model for storing solutions with markdown content and AI-generated summaries.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='solutions')
    tags = models.ManyToManyField(Tag, related_name='solutions', blank=True)
    
    # We'll store the current version's content here for quick access
    content = models.TextField()
    content_html = models.TextField(editable=False, blank=True)
    summary = models.TextField(editable=False, blank=True, help_text="AI-generated summary of the solution")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Solution'
        verbose_name_plural = 'Solutions'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)
            
            # Ensure slug uniqueness
            original_slug = self.slug
            counter = 1
            while Solution.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Generate HTML from markdown
        try:
            # Try with mermaid extension
            self.content_html = markdown.markdown(
                self.content,
                extensions=[
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.tables',
                    'markdown.extensions.toc',
                    'mdx_mermaid',  # Updated to use mdx_mermaid (markdown-mermaid package)
                ]
            )
        except ImportError:
            # Fallback without mermaid extension
            self.content_html = markdown.markdown(
                self.content,
                extensions=[
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.tables',
                    'markdown.extensions.toc',
                ]
            )

        # Generate summary if this is a new solution or content has changed
        if not self.pk or 'content' in kwargs.get('update_fields', []) or kwargs.get('force_summary', False):
            from .ai_services import generate_summary
            self.summary = generate_summary(self.content)

            # Make sure summary is included in update_fields if it's being used
            if 'update_fields' in kwargs:
                kwargs['update_fields'] = list(kwargs['update_fields']) + ['summary']

        # Remove force_summary from kwargs if it exists
        kwargs.pop('force_summary', None)

        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('solutions:detail', kwargs={'slug': self.slug})
    
    def get_latest_version(self):
        return self.versions.order_by('-created_at').first()
    
    def get_version_count(self):
        return self.versions.count()
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def get_average_rating(self):
        """Returns the average rating for this solution."""
        avg = self.ratings.aggregate(Avg('value'))['value__avg']
        if avg is not None:
            return round(avg, 1)
        return 0

    def get_rating_count(self):
        """Returns the number of ratings for this solution."""
        return self.ratings.count()

    def user_has_rated(self, user):
        """Check if a user has already rated this solution."""
        if user.is_authenticated:
            return self.ratings.filter(user=user).exists()
        return False

    def get_user_rating(self, user):
        """Get a specific user's rating for this solution."""
        if user.is_authenticated:
            try:
                return self.ratings.get(user=user).value
            except:
                return None
        return None


class SolutionVersion(models.Model):
    """
    Model for tracking version history of solutions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='solution_versions')
    version_number = models.PositiveIntegerField(editable=False)
    change_comment = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-version_number']
        verbose_name = 'Solution Version'
        verbose_name_plural = 'Solution Versions'
        unique_together = [['solution', 'version_number']]
    
    def __str__(self):
        return f"{self.solution.title} - v{self.version_number}"
    
    def save(self, *args, **kwargs):
        # Auto-increment version number
        if not self.version_number:
            latest_version = self.solution.versions.order_by('-version_number').first()
            self.version_number = 1 if not latest_version else latest_version.version_number + 1
        
        super().save(*args, **kwargs)
    
    def get_diff_to_previous(self):
        """
        Get a diff between this version and the previous version.
        """
        if self.version_number == 1:
            return None
        
        previous_version = self.solution.versions.filter(
            version_number=self.version_number - 1
        ).first()
        
        if not previous_version:
            return None
        
        diff = difflib.unified_diff(
            previous_version.content.splitlines(),
            self.content.splitlines(),
            lineterm='',
            n=3
        )
        
        return '\n'.join(diff)
