from django.contrib import admin
from django.utils.html import format_html
from .models import Solution, SolutionVersion


class SolutionVersionInline(admin.TabularInline):
    model = SolutionVersion
    extra = 0
    readonly_fields = ('version_number', 'created_at', 'created_by')
    fields = ('version_number', 'change_comment', 'created_at', 'created_by')
    can_delete = False
    max_num = 0  # Don't allow adding new versions through the admin
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'updated_at', 'is_published', 'view_count', 'tag_list')
    list_filter = ('is_published', 'created_at', 'updated_at', 'tags')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'view_count', 'content_html_preview')
    filter_horizontal = ('tags',)
    date_hierarchy = 'created_at'
    inlines = [SolutionVersionInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'tags')
        }),
        ('Content', {
            'fields': ('content', 'content_html_preview')
        }),
        ('Metadata', {
            'fields': ('is_published', 'view_count', 'created_at', 'updated_at')
        }),
    )
    
    def tag_list(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    tag_list.short_description = 'Tags'
    
    def content_html_preview(self, obj):
        if obj.content_html:
            return format_html('<div style="max-height: 300px; overflow-y: auto;">{}</div>', obj.content_html)
        return "-"
    content_html_preview.short_description = 'Rendered HTML'


@admin.register(SolutionVersion)
class SolutionVersionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'solution', 'version_number', 'created_by', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('solution__title', 'change_comment', 'content')
    readonly_fields = ('solution', 'version_number', 'created_at', 'created_by', 'content_preview')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('solution', 'version_number', 'created_by', 'created_at', 'change_comment')
        }),
        ('Content', {
            'fields': ('content', 'content_preview')
        }),
    )
    
    def content_preview(self, obj):
        return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', obj.content)
    content_preview.short_description = 'Content Preview'
    
    def has_add_permission(self, request):
        return False  # Don't allow adding versions directly through the admin
