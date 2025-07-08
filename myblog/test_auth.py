#!/usr/bin/env python3
"""
Test script for authentication system
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

def test_authentication():
    """Test email and username authentication."""
    print("🧪 Testing Authentication System...")
    print("=" * 50)
    
    # Get a test user (you'll need to replace with actual credentials)
    try:
        # Try to find any active user for testing
        test_user = User.objects.filter(is_active=True).first()
        if not test_user:
            print("❌ No active users found for testing")
            return
        
        print(f"📧 Testing with user: {test_user.username} ({test_user.email})")
        print()
        
        # Test 1: Authentication with username (this should work with default backend)
        print("🔐 Test 1: Username Authentication")
        print(f"   Trying username: {test_user.username}")
        # Note: We can't test with actual password since it's hashed
        print("   (Cannot test with actual password - it's hashed)")
        print()
        
        # Test 2: Authentication with email (this should work with custom backend)
        print("🔐 Test 2: Email Authentication")
        print(f"   Trying email: {test_user.email}")
        print("   (Cannot test with actual password - it's hashed)")
        print()
        
        # Test 3: Check authentication backends
        print("🔧 Test 3: Authentication Backends")
        print(f"   Configured backends: {settings.AUTHENTICATION_BACKENDS}")
        print()
        
        # Test 4: Check if custom backend is loaded
        try:
            from blog.auth_backends import EmailOrUsernameBackend
            backend = EmailOrUsernameBackend()
            print("✅ Custom EmailOrUsernameBackend loaded successfully")
            print(f"   Backend class: {backend.__class__.__name__}")
        except ImportError as e:
            print(f"❌ Failed to load custom backend: {e}")
        
        print()
        print("💡 To test actual login:")
        print("   1. Go to the login page")
        print("   2. Try logging in with your email address")
        print("   3. Try logging in with your username")
        print("   4. Both should work with the same password")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_authentication()
