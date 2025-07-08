from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from .models import Post, Tag
from django.core.exceptions import ValidationError
import re


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "First Name (letters only)"
        }),
        help_text="Only letters are allowed, no numbers or special characters."
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Last Name (letters only)"
        }),
        help_text="Only letters are allowed, no numbers or special characters."
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Email Address"
        }),
        help_text="A valid email address is required for account verification."
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Tell us about yourself (optional)"
        }),
        required=False
    )
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2", "bio", "profile_picture"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Update field attributes
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username (unique)'
        })
        self.fields['username'].help_text = "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."

        for name, field in self.fields.items():
            if field.widget.__class__.__name__ not in ['CheckboxInput', 'ClearableFileInput', 'FileInput']:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'

    def clean_username(self):
        """Validate username uniqueness."""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose a different one.")
        return username

    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists. Please use a different email or try logging in.")
        return email

    def clean_first_name(self):
        """Validate first name contains only letters."""
        first_name = self.cleaned_data.get('first_name')
        if not re.match(r'^[a-zA-Z\s]+$', first_name):
            raise ValidationError("First name can only contain letters and spaces.")
        return first_name.title()  # Capitalize properly

    def clean_last_name(self):
        """Validate last name contains only letters."""
        last_name = self.cleaned_data.get('last_name')
        if not re.match(r'^[a-zA-Z\s]+$', last_name):
            raise ValidationError("Last name can only contain letters and spaces.")
        return last_name.title()  # Capitalize properly

    def save(self, commit=True):
        """Save user as inactive until email verification."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = False  # User will be activated after email verification

        if commit:
            user.save()
        return user

# blog/forms.py
from django import forms
from .models import Post, Tag

class PostForm(forms.ModelForm):
    # Text field for user search with autocomplete
    tagged_authors_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Type to search and tag users...",
            "id": "user-search-input"
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
        fields = ["title", "content", "image", "tags", "new_tags"]
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
            'placeholder': 'Username or Email',
        })
        self.fields['username'].label = 'Username or Email'
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })


class EmailVerificationForm(forms.Form):
    """Form for email OTP verification."""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '000000',
            'style': 'font-size: 1.5rem; letter-spacing: 0.5rem;',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'title': 'Please enter a 6-digit OTP'
        }),
        help_text="Enter the 6-digit code sent to your email address."
    )


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset via email."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
        }),
        help_text="Enter the email address associated with your account"
    )

    def clean_email(self):
        """Validate that email exists in the system."""
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email, is_active=True).exists():
            raise ValidationError("No active account found with this email address.")
        return email


class PasswordResetVerifyForm(forms.Form):
    """Form for verifying OTP during password reset."""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
        }),
        help_text="Enter the 6-digit code sent to your email"
    )


class PasswordResetConfirmForm(forms.Form):
    """Form for setting new password after OTP verification."""
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password',
        }),
        help_text="Password must be at least 8 characters long"
    )

    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        }),
        help_text="Enter the same password as above for verification"
    )

    def clean(self):
        """Validate that both passwords match."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2:
            if password1 != password2:
                raise ValidationError("The two password fields didn't match.")

            # Validate password strength
            if len(password1) < 8:
                raise ValidationError("Password must be at least 8 characters long.")

            if password1.isdigit():
                raise ValidationError("Password cannot be entirely numeric.")

            if password1.lower() in ['password', '12345678', 'qwerty']:
                raise ValidationError("Password is too common.")

        return cleaned_data

    def clean_otp_code(self):
        """Validate OTP format."""
        otp_code = self.cleaned_data.get('otp_code')
        if not re.match(r'^\d{6}$', otp_code):
            raise ValidationError("OTP must be exactly 6 digits.")
        return otp_code

