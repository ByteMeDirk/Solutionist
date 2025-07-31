from django import forms
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError
from .ratings import Rating
from .models import Solution, SolutionVersion
from tags.models import Tag


class SolutionForm(forms.ModelForm):
    """
    Form for creating and editing solutions.
    """
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 15,
            'placeholder': 'Write your solution using Markdown...'
        }),
        validators=[MinLengthValidator(10, message="Content must be at least 10 characters long.")]
    )

    # Replace ModelMultipleChoiceField with CharField for custom tag input
    tags_input = forms.CharField(
        required=True,
        label="Tags",
        help_text="Enter at least 5 tags separated by commas (e.g., python,django,api,rest,database)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tags separated by commas',
            'data-role': 'tagsinput'
        })
    )

    # Add change_comment field for tracking version changes when editing
    change_comment = forms.CharField(
        required=False,
        label="Change Comment",
        help_text="Briefly describe what you changed (optional)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Fixed code example, Updated API documentation'
        }),
        max_length=255
    )

    class Meta:
        model = Solution
        fields = ['title', 'content', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Solution title'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # If we're editing an existing solution, pre-populate the tags input
        if instance:
            self.initial['tags_input'] = ', '.join([tag.name for tag in instance.tags.all()])

        # Make change_comment field required only when editing existing solutions
        if instance:
            self.fields['change_comment'].required = True

    def clean_tags_input(self):
        """Validate that at least 5 tags are provided."""
        tags_text = self.cleaned_data.get('tags_input', '').strip()
        tag_list = [t.strip() for t in tags_text.split(',') if t.strip()]

        if len(tag_list) < 5:
            raise ValidationError("Please provide at least 5 tags to categorize your solution.")

        return tags_text

    def save(self, commit=True):
        solution = super().save(commit=False)

        if not solution.pk:  # New solution
            solution.author = self.user

        if commit:
            solution.save()

            # Process tags
            if 'tags_input' in self.cleaned_data:
                tags_text = self.cleaned_data['tags_input']
                tag_names = [tag.strip() for tag in tags_text.split(',') if tag.strip()]

                # Clear existing tags if editing
                solution.tags.clear()

                # Add tags, creating new ones if needed
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    solution.tags.add(tag)

            # Create a version record for this save
            SolutionVersion.objects.create(
                solution=solution,
                content=solution.content,
                created_by=self.user,
                change_comment=self.cleaned_data.get('change_comment', "Updated solution")
            )

        return solution


class SolutionVersionCompareForm(forms.Form):
    """
    Form for comparing two versions of a solution.
    """
    version_a = forms.UUIDField(widget=forms.Select(), required=True)
    version_b = forms.UUIDField(widget=forms.Select(), required=True)

    def __init__(self, solution, *args, **kwargs):
        super().__init__(*args, **kwargs)
        versions = solution.versions.all()
        choices = [(str(v.id), f"Version {v.version_number} - {v.created_at.strftime('%Y-%m-%d %H:%M')}") for v in versions]

        self.fields['version_a'].widget.choices = choices
        self.fields['version_b'].widget.choices = choices

        # Set initial values if not provided
        if not self.initial.get('version_a') and len(choices) > 1:
            self.initial['version_a'] = choices[1][0]  # Second latest version

        if not self.initial.get('version_b') and choices:
            self.initial['version_b'] = choices[0][0]  # Latest version


class RatingForm(forms.ModelForm):
    """
    Form for users to rate solutions on a scale of 1-5 stars.
    """
    value = forms.ChoiceField(
        choices=Rating.RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'star-rating'})
    )

    class Meta:
        model = Rating
        fields = ['value']


class SolutionSearchForm(forms.Form):
    """
    Form for searching solutions with various filters.
    """
    query = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search solutions...'
        })
    )
    tags = forms.CharField(
        required=False,
        label='Tags',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tags (comma separated)',
            'data-role': 'tagsinput'
        })
    )
    sort_by = forms.ChoiceField(
        required=False,
        label='Sort by',
        choices=[
            ('', 'Relevance'),
            ('date_desc', 'Newest first'),
            ('date_asc', 'Oldest first'),
            ('rating_desc', 'Highest rated'),
            ('views_desc', 'Most viewed'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
