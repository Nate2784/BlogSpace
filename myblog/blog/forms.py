from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    bio = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control"}), required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2", "bio", "profile_picture"]

from .models import Post, Tag

from django import forms
from django.contrib.auth.models import User
from .models import Post, Tag

from django import forms
from .models import Post, Tag

class PostForm(forms.ModelForm):
    new_tags = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={"placeholder": "Enter new tags, comma-separated"})
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"})
    )

    class Meta:
        model = Post
        fields = ["title", "content", "image", "tags", "new_tags"]
