"""
Utility functions for the blog application.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_verification_email(user, otp_code):
    """
    Send email verification OTP to user.
    
    Args:
        user: User instance
        otp_code: 6-digit OTP code
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = 'BlogSpace - Verify Your Email Address'
        
        # Create HTML email content
        html_message = render_to_string('blog/emails/verification_email.html', {
            'user': user,
            'otp_code': otp_code,
            'site_name': 'BlogSpace'
        })
        
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False


def send_welcome_email(user):
    """
    Send welcome email after successful verification.
    
    Args:
        user: User instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = 'Welcome to BlogSpace!'
        
        # Create HTML email content
        html_message = render_to_string('blog/emails/welcome_email.html', {
            'user': user,
            'site_name': 'BlogSpace'
        })
        
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user, otp_code):
    """Send password reset email with OTP code."""
    try:
        subject = 'BlogSpace - Reset Your Password'

        # Render HTML email template
        html_message = render_to_string('blog/emails/password_reset_email.html', {
            'user': user,
            'otp_code': otp_code,
            'site_name': 'BlogSpace'
        })

        # Create plain text version
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Password reset email sent successfully to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def send_password_reset_success_email(user):
    """Send confirmation email after successful password reset."""
    try:
        subject = 'BlogSpace - Password Reset Successful'

        # Render HTML email template
        html_message = render_to_string('blog/emails/password_reset_success_email.html', {
            'user': user,
            'site_name': 'BlogSpace'
        })

        # Create plain text version
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Password reset success email sent to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset success email to {user.email}: {str(e)}")
        return False


def format_otp_for_display(otp_code):
    """
    Format OTP code for better display (e.g., "123 456").
    
    Args:
        otp_code: 6-digit OTP string
    
    Returns:
        str: Formatted OTP code
    """
    if len(otp_code) == 6:
        return f"{otp_code[:3]} {otp_code[3:]}"
    return otp_code


def validate_name_field(name):
    """
    Validate that a name field contains only letters and spaces.
    
    Args:
        name: Name string to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    import re
    
    if not name:
        return False, "Name cannot be empty."
    
    if not re.match(r'^[a-zA-Z\s]+$', name):
        return False, "Name can only contain letters and spaces."
    
    if len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long."
    
    if len(name.strip()) > 30:
        return False, "Name cannot be longer than 30 characters."
    
    return True, ""


def clean_username(username):
    """
    Clean and validate username.
    
    Args:
        username: Username string
    
    Returns:
        tuple: (is_valid, cleaned_username, error_message)
    """
    if not username:
        return False, "", "Username cannot be empty."
    
    # Remove extra spaces and convert to lowercase
    cleaned = username.strip().lower()
    
    if len(cleaned) < 3:
        return False, cleaned, "Username must be at least 3 characters long."
    
    if len(cleaned) > 150:
        return False, cleaned, "Username cannot be longer than 150 characters."
    
    # Check for valid characters
    import re
    if not re.match(r'^[a-zA-Z0-9@.+_-]+$', cleaned):
        return False, cleaned, "Username can only contain letters, numbers, and @/./+/-/_ characters."
    
    return True, cleaned, ""
