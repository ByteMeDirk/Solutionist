from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    """
    Form for users to add comments to solutions.
    """

    content = forms.CharField(
        label="",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Add your comment here...",
                "rows": 4,
            }
        ),
    )

    class Meta:
        model = Comment
        fields = ["content"]


class ReplyForm(forms.ModelForm):
    """
    Form for users to reply to existing comments.
    """

    content = forms.CharField(
        label="",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Add your reply here...",
                "rows": 2,
            }
        ),
    )

    class Meta:
        model = Comment
        fields = ["content"]
