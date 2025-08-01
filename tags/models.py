from django.db import models
from django.utils.text import slugify


class Tag(models.Model):
    """
    Model for categorizing solutions with tags.
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Only create slug if it doesn't exist yet, preserve the original name case
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def get_or_create_tags(cls, tag_names):
        """
        Get or create tags from a list of names.
        Handles case sensitivity and returns a list of Tag objects.
        """
        tags = []
        for name in tag_names:
            name = name.strip()
            if name:
                # Normalize the name for case-insensitive lookup
                normalized_name = name.lower()
                tag, created = cls.objects.get_or_create(
                    name__iexact=normalized_name,
                    defaults={"name": name, "slug": slugify(name)},
                )
                tags.append(tag)
        return tags
