from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import PostView, Post, UserAnalytics
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class PostViewTrackingMiddleware(MiddlewareMixin):
    """Middleware to track post views for analytics."""
    
    def process_request(self, request):
        # Only track views for post detail pages
        try:
            resolved = resolve(request.path)
            print(f"Middleware called for: {request.path}, url_name: {resolved.url_name}")
            if resolved.url_name == 'post_detail':
                post_id = resolved.kwargs.get('post_id')
                if post_id:
                    print(f"Tracking view for post {post_id}")
                    self.track_post_view(request, post_id)
        except Exception as e:
            print(f"Middleware error: {e}")

        return None
    
    def track_post_view(self, request, post_id):
        """Track a post view with intelligent throttling."""
        try:
            post = Post.objects.get(id=post_id)
            user = request.user if request.user.is_authenticated else None
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Different throttling rules for different scenarios
            if user and user.is_authenticated:
                # For authenticated users: 15 minutes throttling
                throttle_time = timezone.now() - timedelta(minutes=15)
                recent_view = PostView.objects.filter(
                    post=post,
                    user=user,
                    viewed_at__gte=throttle_time
                ).first()
                identifier = f"user:{user.username}"
            else:
                # For anonymous users: 30 minutes throttling by IP
                throttle_time = timezone.now() - timedelta(minutes=30)
                recent_view = PostView.objects.filter(
                    post=post,
                    user=None,
                    ip_address=ip_address,
                    viewed_at__gte=throttle_time
                ).first()
                identifier = f"ip:{ip_address}"

            # Only create a new view if no recent view exists
            if not recent_view:
                PostView.objects.create(
                    post=post,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                print(f"✅ View tracked: '{post.title}' by {identifier}")

                # Update analytics immediately
                try:
                    analytics, created = UserAnalytics.objects.get_or_create(user=post.author)
                    analytics.update_analytics()
                except Exception as e:
                    print(f"Analytics update error: {e}")

            else:
                print(f"⏱️ View throttled: '{post.title}' by {identifier} (viewed {recent_view.viewed_at})")

        except Post.DoesNotExist:
            print(f"❌ Post {post_id} not found")
        except Exception as e:
            print(f"❌ Error tracking view: {e}")
    
    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '127.0.0.1'
