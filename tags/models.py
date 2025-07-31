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
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Convert name to lowercase before saving
        self.name = self.name.lower()
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
            name = name.strip().lower()
            if name:
                tag, _ = cls.objects.get_or_create(
                    name=name,
                    defaults={'slug': slugify(name)}
                )
                tags.append(tag)
        return tags
