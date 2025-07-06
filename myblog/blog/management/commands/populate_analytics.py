from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import Post, PostView, UserAnalytics
import random
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Populate sample analytics data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Populating analytics data...')
        
        # Get all posts
        posts = Post.objects.all()
        users = User.objects.all()
        
        if not posts.exists():
            self.stdout.write(self.style.WARNING('No posts found. Create some posts first.'))
            return
        
        # Generate sample views for the last 30 days
        for post in posts:
            for i in range(30):
                date = timezone.now() - timedelta(days=i)
                
                # Generate random number of views for each day (0-20)
                daily_views = random.randint(0, 20)
                
                for j in range(daily_views):
                    # Create view with random IP and optional user
                    user = random.choice(users) if random.random() > 0.3 else None
                    ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"

                    # Use get_or_create to avoid unique constraint violations
                    view, created = PostView.objects.get_or_create(
                        post=post,
                        user=user,
                        ip_address=ip,
                        defaults={'user_agent': "Sample User Agent"}
                    )

                    if created:
                        # Manually set the created date
                        view.viewed_at = date - timedelta(
                            hours=random.randint(0, 23),
                            minutes=random.randint(0, 59)
                        )
                        view.save()
        
        # Update analytics for all users
        for user in users:
            analytics, created = UserAnalytics.objects.get_or_create(user=user)
            analytics.update_analytics()
            
        self.stdout.write(
            self.style.SUCCESS('Successfully populated analytics data!')
        )
