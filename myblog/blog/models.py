from django.db import models
from django.contrib.auth.models import User

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
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Comment by {self.user} on {self.post}'

