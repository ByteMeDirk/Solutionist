from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import UserProfile, UserSettings


class UserRegistrationForm(UserCreationForm):
    """
    Form for user registration with additional fields.
    """

    email = forms.EmailField(
        required=True, help_text="Required. Enter a valid email address."
    )
    first_name = forms.CharField(max_length=30, required=False, help_text="Optional.")
    last_name = forms.CharField(max_length=30, required=False, help_text="Optional.")

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()

        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form with Bootstrap styling.
    """

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        )
    )


class UserProfileForm(forms.ModelForm):
    """
    Form for editing user profile information.
    """

    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = (
            "profile_image",
            "bio",
            "skills",
            "experience",
            "website",
            "github",
            "twitter",
            "linkedin",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "skills": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Python, Django, JavaScript, etc.",
                }
            ),
            "experience": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "website": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://example.com"}
            ),
            "github": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://github.com/username",
                }
            ),
            "twitter": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://twitter.com/username",
                }
            ),
            "linkedin": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://linkedin.com/in/username",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)

        # Update the related User model fields
        user = profile.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            profile.save()

        return profile


class UserDeleteForm(forms.Form):
    """
    Form for confirming user account deletion.
    """

    password = forms.CharField(
        label="Enter your password to confirm deletion",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
    )

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not self.user.check_password(password):
            raise ValidationError("Incorrect password. Please try again.")
        return password


class UserSettingsForm(forms.ModelForm):
    """
    Form for managing user settings related to theme and accessibility
    """

    class Meta:
        model = UserSettings
        fields = ["theme", "font_size", "reduced_motion", "high_contrast"]
        widgets = {
            "theme": forms.RadioSelect(),
            "font_size": forms.RadioSelect(),
            "reduced_motion": forms.CheckboxInput(),
            "high_contrast": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["theme"].help_text = "Choose your preferred theme for the site"
        self.fields["font_size"].help_text = "Select your preferred text size"
        # Make labels more user-friendly
        self.fields["reduced_motion"].label = "Reduce animations"
        self.fields["high_contrast"].label = "High contrast mode"
