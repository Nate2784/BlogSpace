from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)

    def get_author_posts(self):
        return Post.objects.filter(author=self.user)

    def __str__(self):
        return self.user.username


class Tag(models.Model):
    """Category tags for blog posts."""
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    tagged_authors = models.ManyToManyField(User, related_name="tagged_posts", blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    image = models.ImageField(upload_to='post_images/', blank=True)  # New image field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)

    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Comment model for posts."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.user} on {self.post}'

    def is_reply(self):
        return self.parent is not None


class PostView(models.Model):
    """Track post views for analytics."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="views")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # null for anonymous users
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']

    def __str__(self):
        return f'View of {self.post.title} by {self.user or self.ip_address}'


class UserAnalytics(models.Model):
    """Store aggregated analytics data for users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="analytics")
    total_post_views = models.PositiveIntegerField(default=0)
    total_likes_received = models.PositiveIntegerField(default=0)
    total_comments_received = models.PositiveIntegerField(default=0)
    total_followers = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Analytics for {self.user.username}'

    def update_analytics(self):
        """Update analytics data for this user."""
        # Calculate total views across all posts
        self.total_post_views = PostView.objects.filter(post__author=self.user).count()

        # Calculate total likes received using PostLike model
        self.total_likes_received = PostLike.objects.filter(post__author=self.user).count()

        # Calculate total comments received
        self.total_comments_received = Comment.objects.filter(post__author=self.user).count()

        # Calculate followers (unique users who liked at least one post)
        followers = PostLike.objects.filter(post__author=self.user).values_list('user', flat=True).distinct()
        self.total_followers = followers.count()

        self.save()


class PostLike(models.Model):
    """Track post likes with timestamps for better analytics."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']

    def __str__(self):
        return f'{self.user.username} liked {self.post.title}'


class DailyAnalytics(models.Model):
    """Store daily analytics data."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_analytics")
    date = models.DateField()
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    new_posts = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f'Daily analytics for {self.user.username} on {self.date}'

