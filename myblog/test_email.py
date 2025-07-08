#!/usr/bin/env python3
"""
Test script to diagnose email sending issues
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')
django.setup()

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_django_email():
    """Test Django email sending"""
    print("🧪 Testing Django Email Configuration...")
    print(f"📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📧 Email Host: {settings.EMAIL_HOST}")
    print(f"📧 Email Port: {settings.EMAIL_PORT}")
    print(f"📧 Email Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"📧 Email User: {settings.EMAIL_HOST_USER}")
    print(f"📧 Default From: {settings.DEFAULT_FROM_EMAIL}")
    print()
    
    try:
        # Test simple email
        result = send_mail(
            subject='BlogSpace Test Email',
            message='This is a test email from BlogSpace to verify email configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
            fail_silently=False,
        )
        
        if result:
            print("✅ Django email sent successfully!")
            return True
        else:
            print("❌ Django email failed to send")
            return False
            
    except Exception as e:
        print(f"❌ Django email error: {str(e)}")
        return False

def test_smtp_direct():
    """Test SMTP connection directly"""
    print("\n🔧 Testing Direct SMTP Connection...")
    
    try:
        # Create SMTP connection
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls()
        
        print("✅ SMTP connection established")
        
        # Login
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("✅ SMTP login successful")
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = settings.EMAIL_HOST_USER
        msg['Subject'] = "BlogSpace Direct SMTP Test"
        
        body = "This is a direct SMTP test from BlogSpace."
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        print("✅ Direct SMTP email sent successfully!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error: {str(e)}")
        print("💡 Check your Gmail App Password")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ General Error: {str(e)}")
        return False

def test_otp_email():
    """Test OTP email template"""
    print("\n📧 Testing OTP Email Template...")
    
    try:
        # Create fake user data for testing
        user_data = {
            'first_name': 'Test',
            'email': settings.EMAIL_HOST_USER
        }
        
        # Create a simple user-like object
        class FakeUser:
            def __init__(self, data):
                self.first_name = data['first_name']
                self.email = data['email']
        
        fake_user = FakeUser(user_data)
        otp_code = "123456"
        
        # Render email template
        html_message = render_to_string('blog/emails/verification_email.html', {
            'user': fake_user,
            'otp_code': otp_code,
            'site_name': 'BlogSpace'
        })
        
        plain_message = strip_tags(html_message)
        
        # Send OTP email
        result = send_mail(
            subject='BlogSpace - Verify Your Email Address',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[fake_user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if result:
            print("✅ OTP email template sent successfully!")
            print(f"📧 Sent to: {fake_user.email}")
            print(f"🔑 Test OTP: {otp_code}")
            return True
        else:
            print("❌ OTP email failed to send")
            return False
            
    except Exception as e:
        print(f"❌ OTP email error: {str(e)}")
        return False

def check_gmail_settings():
    """Check Gmail account settings"""
    print("\n🔍 Gmail Account Settings Check...")
    print("Please verify the following Gmail settings:")
    print()
    print("1. ✅ 2-Factor Authentication is ENABLED")
    print("2. ✅ App Password is generated and valid")
    print("3. ✅ 'Less secure app access' is NOT needed (we use App Password)")
    print("4. ✅ Account is not locked or suspended")
    print()
    print("📱 To generate a new App Password:")
    print("   1. Go to https://myaccount.google.com/")
    print("   2. Security → 2-Step Verification → App passwords")
    print("   3. Generate new password for 'Mail'")
    print("   4. Use the 16-character password (no spaces)")
    print()

def main():
    """Run all email tests"""
    print("🚀 BlogSpace Email Diagnostic Tool")
    print("=" * 50)
    
    # Check Gmail settings
    check_gmail_settings()
    
    # Test 1: Django email
    django_success = test_django_email()
    
    # Test 2: Direct SMTP
    smtp_success = test_smtp_direct()
    
    # Test 3: OTP email template
    if django_success:
        otp_success = test_otp_email()
    else:
        print("\n⏭️ Skipping OTP test due to Django email failure")
        otp_success = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Django Email: {'✅ PASS' if django_success else '❌ FAIL'}")
    print(f"Direct SMTP: {'✅ PASS' if smtp_success else '❌ FAIL'}")
    print(f"OTP Template: {'✅ PASS' if otp_success else '❌ FAIL'}")
    print()
    
    if all([django_success, smtp_success, otp_success]):
        print("🎉 All tests passed! Email should be working.")
    else:
        print("🔧 Some tests failed. Check the errors above.")
        print()
        print("💡 Common solutions:")
        print("   1. Generate a new Gmail App Password")
        print("   2. Check if 2FA is enabled on Gmail")
        print("   3. Verify email/password in .env file")
        print("   4. Check Gmail account security settings")

if __name__ == "__main__":
    main()
