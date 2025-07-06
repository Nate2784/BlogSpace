from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import Post, PostView, PostLike, Comment, UserAnalytics
import random


class Command(BaseCommand):
    help = 'Test analytics updates by creating sample data'

    def handle(self, *args, **options):
        self.stdout.write('Testing analytics updates...')
        
        # Get a user and post for testing
        user = User.objects.first()
        post = Post.objects.first()
        
        if not user or not post:
            self.stdout.write(self.style.ERROR('No users or posts found. Create some first.'))
            return
        
        # Get initial analytics
        analytics, created = UserAnalytics.objects.get_or_create(user=post.author)
        initial_views = analytics.total_post_views
        initial_likes = analytics.total_likes_received
        initial_comments = analytics.total_comments_received
        
        self.stdout.write(f'Initial stats for {post.author.username}:')
        self.stdout.write(f'  Views: {initial_views}')
        self.stdout.write(f'  Likes: {initial_likes}')
        self.stdout.write(f'  Comments: {initial_comments}')
        
        # Create a test view
        test_view, created = PostView.objects.get_or_create(
            post=post,
            user=user,
            ip_address=f"192.168.1.{random.randint(100, 200)}",
            defaults={'user_agent': 'Test User Agent'}
        )
        
        if created:
            self.stdout.write('Created test view')
        
        # Create a test like
        test_like, created = PostLike.objects.get_or_create(
            post=post,
            user=user
        )
        
        if created:
            self.stdout.write('Created test like')
        
        # Create a test comment
        test_comment = Comment.objects.create(
            post=post,
            user=user,
            text='Test comment for analytics'
        )
        self.stdout.write('Created test comment')
        
        # Check updated analytics
        analytics.refresh_from_db()
        analytics.update_analytics()
        
        self.stdout.write(f'Updated stats for {post.author.username}:')
        self.stdout.write(f'  Views: {analytics.total_post_views} (change: +{analytics.total_post_views - initial_views})')
        self.stdout.write(f'  Likes: {analytics.total_likes_received} (change: +{analytics.total_likes_received - initial_likes})')
        self.stdout.write(f'  Comments: {analytics.total_comments_received} (change: +{analytics.total_comments_received - initial_comments})')
        
        self.stdout.write(self.style.SUCCESS('Analytics test completed!'))
