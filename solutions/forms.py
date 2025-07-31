from django import forms
from django.contrib.auth import get_user_model
from markdownx.fields import MarkdownxFormField
from markdownx.widgets import MarkdownxWidget

from .models import Solution, SolutionVersion
from tags.models import Tag


class SolutionForm(forms.ModelForm):
    """
    Form for creating and editing solutions.
    """
    content = MarkdownxFormField(
        widget=MarkdownxWidget(
            attrs={
                'class': 'form-control',
                'data-markdownx-editor-resizable': 'true',
                'data-markdownx-urls-path': '/markdownx/upload/',
                'rows': '20',
            }
        )
    )
    
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tags separated by commas',
        }),
        help_text='Enter tags separated by commas (e.g., python, django, web)'
    )
    
    change_comment = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brief description of changes (optional)',
        }),
        help_text='Briefly describe what changed in this version'
    )
    
    class Meta:
        model = Solution
        fields = ['title', 'content', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If editing an existing solution, populate tags_input
        if self.instance.pk:
            self.fields['tags_input'].initial = ', '.join([tag.name for tag in self.instance.tags.all()])
    
    def clean_tags_input(self):
        """
        Process the tags_input field to create or get Tag objects.
        """
        tags_input = self.cleaned_data.get('tags_input', '')
        if not tags_input:
            return []
        
        tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
        tags = []
        
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        
        return tags
    
    def save(self, commit=True):
        """
        Save the solution and create a new version.
        """
        # Set the author if this is a new solution
        if not self.instance.pk and self.user:
            self.instance.author = self.user
        
        solution = super().save(commit=commit)
        
        # Add tags
        if commit:
            tags = self.cleaned_data.get('tags_input', [])
            if tags:
                solution.tags.clear()
                solution.tags.add(*tags)
            
            # Create a new version
            change_comment = self.cleaned_data.get('change_comment', '')
            SolutionVersion.objects.create(
                solution=solution,
                content=solution.content,
                created_by=self.user or solution.author,
                change_comment=change_comment
            )
        
        return solution


class SolutionVersionCompareForm(forms.Form):
    """
    Form for comparing two versions of a solution.
    """
    version_a = forms.ModelChoiceField(
        queryset=SolutionVersion.objects.none(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    version_b = forms.ModelChoiceField(
        queryset=SolutionVersion.objects.none(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, solution, *args, **kwargs):
        super().__init__(*args, **kwargs)
        versions = solution.versions.all().order_by('-version_number')
        
        self.fields['version_a'].queryset = versions
        self.fields['version_b'].queryset = versions
        
        # Default to comparing the latest two versions
        if versions.count() >= 2:
            self.fields['version_a'].initial = versions[0].pk
            self.fields['version_b'].initial = versions[1].pk