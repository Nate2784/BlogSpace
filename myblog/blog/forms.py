from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from .models import Post, Tag


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    bio = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control"}), required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2", "bio", "profile_picture"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():  # <- unpack here
            if field.widget.__class__.__name__ not in ['CheckboxInput', 'ClearableFileInput', 'FileInput']:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'

# blog/forms.py
from django import forms
from .models import Post, Tag

class PostForm(forms.ModelForm):
    # Allow selecting multiple authors to tag
    tagged_authors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            "class": "form-select",
            "size": "6"  # Show 6 options at once
        })
    )

    # Existing tags selection
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            "class": "form-select",
            "size": "6"  # Show 6 options at once
        })
    )

    # Text field for users to type new tags
    new_tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter tags separated by commas"
        })
    )

    class Meta:
        model = Post
        fields = ["title", "content", "image", "tags", "new_tags", "tagged_authors"]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write something about yourself...'}),
        }

# blog/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })

