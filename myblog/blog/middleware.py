from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import PostView, Post
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
        """Track a post view with time-based throttling."""
        try:
            post = Post.objects.get(id=post_id)
            user = request.user if request.user.is_authenticated else None
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Check if this user/IP has viewed this post in the last hour
            one_hour_ago = timezone.now() - timedelta(hours=1)

            recent_view = PostView.objects.filter(
                post=post,
                user=user,
                ip_address=ip_address,
                viewed_at__gte=one_hour_ago
            ).first()

            # Only create a new view if no recent view exists
            if not recent_view:
                PostView.objects.create(
                    post=post,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                print(f"New view tracked: {post.title} by {user or ip_address}")
            else:
                print(f"View throttled: {post.title} by {user or ip_address} (recent view exists)")

        except Post.DoesNotExist:
            pass  # Post doesn't exist, ignore
        except Exception as e:
            print(f"Error tracking view: {e}")  # Debug: Print errors
    
    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '127.0.0.1'
