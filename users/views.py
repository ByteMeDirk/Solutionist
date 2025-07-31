from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta

from .forms import UserRegistrationForm, CustomAuthenticationForm, UserProfileForm, UserDeleteForm
from .models import UserProfile
from solutions.models import Solution
from tags.models import Tag
from .mcp import MCPToken


class RegisterView(CreateView):
    """
    View for user registration.
    """
    template_name = 'users/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('users:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Registration successful. You can now log in.")
        return response


class CustomLoginView(LoginView):
    """
    Custom login view using our styled form.
    """
    template_name = 'users/login.html'
    form_class = CustomAuthenticationForm
    
    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me', False)
        if not remember_me:
            # Session expires when the user closes their browser
            self.request.session.set_expiry(0)
        
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """
    Custom logout view with a success message.
    """
    next_page = reverse_lazy('core:home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)


def user_profile_view(request, username):
    """
    View for displaying other users' profiles with comprehensive statistics and data.
    """
    viewed_user = get_object_or_404(User, username=username)
    profile = viewed_user.profile
    solutions = Solution.objects.filter(
        author=viewed_user,
        is_published=True
    ).select_related('author').prefetch_related('tags', 'ratings')

    # Calculate user statistics
    total_solutions = solutions.count()
    total_views = solutions.aggregate(total_views=Sum('view_count'))['total_views'] or 0
    avg_rating = solutions.annotate(
        avg_rating=Avg('ratings__value')
    ).aggregate(total_avg=Avg('avg_rating'))['total_avg'] or 0

    # Get most used tags
    top_tags = Tag.objects.filter(
        solutions__author=viewed_user,
        solutions__is_published=True
    ).annotate(
        usage_count=Count('solutions')
    ).order_by('-usage_count')[:5]

    # Get recent activity (newest solutions)
    recent_solutions = solutions.order_by('-created_at')[:5]

    # Get top rated solutions
    top_rated_solutions = solutions.annotate(
        avg_rating=Avg('ratings__value')
    ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:5]

    # Get most viewed solutions
    most_viewed_solutions = solutions.order_by('-view_count')[:5]

    context = {
        'viewed_user': viewed_user,
        'profile': profile,
        'solutions': solutions,
        'stats': {
            'total_solutions': total_solutions,
            'total_views': total_views,
            'avg_rating': round(avg_rating, 1),
            'member_days': (timezone.now() - viewed_user.date_joined).days
        },
        'top_tags': top_tags,
        'recent_solutions': recent_solutions,
        'top_rated_solutions': top_rated_solutions,
        'most_viewed_solutions': most_viewed_solutions,
    }

    return render(request, 'users/user_profile.html', context)

@login_required
def profile_view(request):
    """
    View for displaying and updating user profile.
    """
    profile = request.user.profile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'users/profile.html', {
        'form': form,
        'profile': profile
    })


@login_required
def account_delete_view(request):
    """
    View for deleting user account.
    """
    if request.method == 'POST':
        form = UserDeleteForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Your account has been deleted successfully.")
            return redirect('core:home')
    else:
        form = UserDeleteForm(user=request.user)
    
    return render(request, 'users/account_delete.html', {'form': form})


class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset view.
    """
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom password reset confirmation view.
    """
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')


@login_required
def mcp_tokens_view(request):
    """
    View for managing MCP tokens.
    """
    tokens = MCPToken.objects.filter(user=request.user).order_by('-created_at')

    # Build the MCP endpoint URL for display
    host = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    mcp_endpoint = f"{protocol}://{host}/api/mcp/"

    context = {
        'tokens': tokens,
        'mcp_endpoint': mcp_endpoint,
    }
    return render(request, 'users/mcp_tokens.html', context)


@login_required
def create_mcp_token(request):
    """
    View for creating a new MCP token.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        expiry_days = int(request.POST.get('expiry', 365))

        if not name:
            messages.error(request, "Token name is required.")
            return redirect('users:mcp_tokens')

        # Create the token
        token = MCPToken(user=request.user, name=name)

        # Set expiration date if specified
        if expiry_days > 0:
            token.expires_at = timezone.now() + timedelta(days=expiry_days)
        else:
            token.expires_at = None

        token.save()

        # Pass the newly created token to the template for display
        messages.success(request, "MCP token created successfully. Please copy your token now, you won't be able to see it again.")
        return redirect('users:mcp_tokens')

    # If not POST, redirect to tokens page
    return redirect('users:mcp_tokens')


@login_required
def revoke_mcp_token(request, token_id):
    """
    View for revoking an MCP token.
    """
    token = get_object_or_404(MCPToken, id=token_id, user=request.user)

    if request.method == 'POST':
        token.revoke()
        messages.success(request, f"Token '{token.name}' has been revoked.")

    return redirect('users:mcp_tokens')
