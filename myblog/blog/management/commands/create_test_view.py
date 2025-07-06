from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import Post, PostView, UserAnalytics
import random


class Command(BaseCommand):
    help = 'Create a test view to verify analytics updates'

    def handle(self, *args, **options):
        self.stdout.write('Creating test view...')
        
        # Get first post and user
        post = Post.objects.first()
        user = User.objects.first()
        
        if not post:
            self.stdout.write(self.style.ERROR('No posts found.'))
            return
            
        # Get analytics before
        analytics, created = UserAnalytics.objects.get_or_create(user=post.author)
        before_views = analytics.total_post_views
        
        self.stdout.write(f'Views before: {before_views}')
        
        # Create a new view
        PostView.objects.create(
            post=post,
            user=user,
            ip_address=f"192.168.1.{random.randint(1, 255)}",
            user_agent="Test Agent"
        )
        
        self.stdout.write('Created new view')
        
        # Update analytics
        analytics.update_analytics()
        after_views = analytics.total_post_views
        
        self.stdout.write(f'Views after: {after_views}')
        self.stdout.write(f'Difference: {after_views - before_views}')
        
        if after_views > before_views:
            self.stdout.write(self.style.SUCCESS('Analytics updated successfully!'))
        else:
            self.stdout.write(self.style.ERROR('Analytics did not update.'))
