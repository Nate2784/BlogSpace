#!/usr/bin/env python
"""
Demo script to show the improved tagging functionality
Run this script to create sample data for testing the tagging features
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import Post, Tag

def create_demo_data():
    """Create sample users, tags, and posts for testing"""
    
    print("🚀 Creating demo data for tagging functionality...")
    
    # Create sample users
    users = []
    for i, username in enumerate(['alice', 'bob', 'charlie', 'diana'], 1):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': username.capitalize(),
                'last_name': 'Demo'
            }
        )
        if created:
            user.set_password('demo123')
            user.save()
            print(f"✅ Created user: {username}")
        else:
            print(f"👤 User already exists: {username}")
        users.append(user)
    
    # Create sample tags
    tag_names = ['python', 'django', 'web-development', 'tutorial', 'beginner', 'advanced']
    tags = []
    for tag_name in tag_names:
        tag, created = Tag.objects.get_or_create(name=tag_name)
        if created:
            print(f"🏷️  Created tag: {tag_name}")
        else:
            print(f"🏷️  Tag already exists: {tag_name}")
        tags.append(tag)
    
    # Create sample posts with various tagging scenarios
    sample_posts = [
        {
            'title': 'Getting Started with Django',
            'content': 'This is a comprehensive guide to getting started with Django web framework.',
            'author': users[0],  # alice
            'tags': [tags[0], tags[1], tags[3]],  # python, django, tutorial
            'tagged_authors': [users[1], users[2]]  # bob, charlie
        },
        {
            'title': 'Advanced Python Techniques',
            'content': 'Learn advanced Python programming techniques and best practices.',
            'author': users[1],  # bob
            'tags': [tags[0], tags[5]],  # python, advanced
            'tagged_authors': [users[0]]  # alice
        },
        {
            'title': 'Web Development Best Practices',
            'content': 'Essential best practices for modern web development.',
            'author': users[2],  # charlie
            'tags': [tags[2], tags[3]],  # web-development, tutorial
            'tagged_authors': [users[0], users[3]]  # alice, diana
        }
    ]
    
    for post_data in sample_posts:
        post, created = Post.objects.get_or_create(
            title=post_data['title'],
            defaults={
                'content': post_data['content'],
                'author': post_data['author']
            }
        )
        
        if created:
            # Add tags
            post.tags.set(post_data['tags'])
            # Add tagged authors
            post.tagged_authors.set(post_data['tagged_authors'])
            print(f"📝 Created post: {post_data['title']}")
            print(f"   Tags: {', '.join([tag.name for tag in post_data['tags']])}")
            print(f"   Tagged authors: {', '.join([user.username for user in post_data['tagged_authors']])}")
        else:
            print(f"📝 Post already exists: {post_data['title']}")
    
    print("\n🎉 Demo data creation complete!")
    print("\n📋 Summary:")
    print(f"   Users: {User.objects.count()}")
    print(f"   Tags: {Tag.objects.count()}")
    print(f"   Posts: {Post.objects.count()}")
    
    print("\n🔗 You can now:")
    print("   1. Visit http://127.0.0.1:8000/ to see the posts")
    print("   2. Login with any demo user (password: demo123)")
    print("   3. Create new posts with multiple tags and authors")
    print("   4. Edit existing posts to modify tags and authors")

if __name__ == '__main__':
    create_demo_data()
