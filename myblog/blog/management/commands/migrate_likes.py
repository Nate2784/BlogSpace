from django.core.management.base import BaseCommand
from blog.models import Post, PostLike
from django.utils import timezone
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Migrate existing likes to PostLike model with timestamps'

    def handle(self, *args, **options):
        self.stdout.write('Migrating existing likes to PostLike model...')
        
        posts = Post.objects.all()
        migrated_count = 0
        
        for post in posts:
            # Get all users who liked this post
            liked_users = post.likes.all()
            
            for user in liked_users:
                # Create PostLike entry if it doesn't exist
                post_like, created = PostLike.objects.get_or_create(
                    post=post,
                    user=user,
                    defaults={
                        'created_at': timezone.now() - timedelta(
                            days=random.randint(0, 30),
                            hours=random.randint(0, 23),
                            minutes=random.randint(0, 59)
                        )
                    }
                )
                
                if created:
                    migrated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully migrated {migrated_count} likes to PostLike model!')
        )
