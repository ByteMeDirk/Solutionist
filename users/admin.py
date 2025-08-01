from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "get_bio",
    )

    def get_bio(self, instance):
        return (
            instance.profile.bio[:50] + "..."
            if len(instance.profile.bio) > 50
            else instance.profile.bio
        )

    get_bio.short_description = "Bio"

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Register UserProfile model directly as well
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "get_email", "get_skills", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "skills")
    readonly_fields = ("created_at", "updated_at")

    def get_email(self, obj):
        return obj.user.email

    def get_skills(self, obj):
        return obj.skills[:50] + "..." if len(obj.skills) > 50 else obj.skills

    get_email.short_description = "Email"
    get_skills.short_description = "Skills"
