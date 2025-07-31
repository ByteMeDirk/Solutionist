from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView

from .forms import UserRegistrationForm, CustomAuthenticationForm, UserProfileForm, UserDeleteForm
from .models import UserProfile
from solutions.models import Solution


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


def user_profile_view(request, username):
    """
    View for displaying other users' profiles.
    """
    user = get_object_or_404(User, username=username)
    profile = user.profile
    solutions = Solution.objects.filter(author=user).order_by('-created_at')

    return render(request, 'users/profile.html', {
        'profile': profile,
        'solutions': solutions,
        'viewed_user': user
    })

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
