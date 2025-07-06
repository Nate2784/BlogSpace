from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PostView, PostLike, Comment, UserAnalytics


@receiver(post_save, sender=PostView)
def update_analytics_on_view(sender, instance, created, **kwargs):
    """Update user analytics when a new view is recorded."""
    if created:
        # Get or create analytics for the post author
        analytics, created = UserAnalytics.objects.get_or_create(
            user=instance.post.author
        )
        # Update analytics
        analytics.update_analytics()


@receiver(post_save, sender=PostLike)
def update_analytics_on_like(sender, instance, created, **kwargs):
    """Update user analytics when a new like is recorded."""
    if created:
        # Get or create analytics for the post author
        analytics, created = UserAnalytics.objects.get_or_create(
            user=instance.post.author
        )
        # Update analytics
        analytics.update_analytics()


@receiver(post_delete, sender=PostLike)
def update_analytics_on_unlike(sender, instance, **kwargs):
    """Update user analytics when a like is removed."""
    # Get or create analytics for the post author
    analytics, created = UserAnalytics.objects.get_or_create(
        user=instance.post.author
    )
    # Update analytics
    analytics.update_analytics()


@receiver(post_save, sender=Comment)
def update_analytics_on_comment(sender, instance, created, **kwargs):
    """Update user analytics when a new comment is posted."""
    if created:
        # Get or create analytics for the post author
        analytics, created = UserAnalytics.objects.get_or_create(
            user=instance.post.author
        )
        # Update analytics
        analytics.update_analytics()


@receiver(post_delete, sender=Comment)
def update_analytics_on_comment_delete(sender, instance, **kwargs):
    """Update user analytics when a comment is deleted."""
    # Get or create analytics for the post author
    analytics, created = UserAnalytics.objects.get_or_create(
        user=instance.post.author
    )
    # Update analytics
    analytics.update_analytics()
