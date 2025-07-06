from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from datetime import datetime, timedelta
from .models import Post, Profile, Tag, Comment, PostView, UserAnalytics, PostLike, User
from .forms import PostForm, UserUpdateForm, ProfileUpdateForm, LoginForm

def home(request):
    posts = Post.objects.all().order_by("-created_at")[:6]  # Show only the latest 10 posts
    return render(request, "blog/home.html", {"posts": posts})

@login_required
def posts(request):
    query = request.GET.get("q")
    selected_tag = request.GET.get("tag")
    posts = Post.objects.all().order_by("-created_at")
    tags = Tag.objects.all()  # Get all available tags

    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(author__username__icontains=query))

    if selected_tag:
        posts = posts.filter(tags__name__icontains=selected_tag)

    # Pagination: Show first 12 posts
    initial_posts = posts[:6]
    has_more = posts.count() > 6

    return render(request, "blog/posts.html", {
        "posts": initial_posts,
        "tags": tags,
        "query": query,
        "selected_tag": selected_tag,
        "has_more": has_more,
        "total_posts": posts.count()
    })


@login_required
def load_more_posts(request):
    """AJAX endpoint for loading more posts"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    query = request.GET.get("q")
    selected_tag = request.GET.get("tag")
    offset = int(request.GET.get("offset", 0))

    posts = Post.objects.all().order_by("-created_at")

    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(author__username__icontains=query))

    if selected_tag:
        posts = posts.filter(tags__name__icontains=selected_tag)

    # Get next 6 posts starting from offset
    next_posts = posts[offset:offset + 6]
    has_more = posts.count() > offset + 6

    # Render posts as HTML
    from django.template.loader import render_to_string
    posts_html = render_to_string('blog/post_cards.html', {
        'posts': next_posts,
        'user': request.user
    })

    return JsonResponse({
        'posts_html': posts_html,
        'has_more': has_more,
        'new_offset': offset + 6
    })


@login_required
def load_more_author_posts(request, username):
    """AJAX endpoint for loading more posts in author profile"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    author = get_object_or_404(User, username=username)
    post_type = request.GET.get("type", "own")  # "own" or "tagged"
    offset = int(request.GET.get("offset", 0))

    if post_type == "own":
        posts = Post.objects.filter(author=author).order_by("-created_at")
    else:
        posts = Post.objects.filter(tagged_authors=author).order_by("-created_at")

    # Get next 6 posts starting from offset
    next_posts = posts[offset:offset + 6]
    has_more = posts.count() > offset + 6

    # Render posts as HTML
    from django.template.loader import render_to_string
    posts_html = render_to_string('blog/author_post_cards.html', {
        'posts': next_posts,
        'user': request.user,
        'post_type': post_type,
        'author': author
    })

    return JsonResponse({
        'posts_html': posts_html,
        'has_more': has_more,
        'new_offset': offset + 6
    })

from django.contrib.auth.decorators import login_required
# blog/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PostForm
from .models import Post, Tag

def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            # Clear existing tags first to avoid duplicates
            post.tags.clear()

            # Handle existing tags from form
            selected_tags = form.cleaned_data.get("tags")
            if selected_tags:
                post.tags.set(selected_tags)

            # Process new tags without duplicates
            new_tag_names = request.POST.get("new_tags", "").strip()
            if new_tag_names:
                tag_list = {tag.strip() for tag in new_tag_names.split(",") if tag.strip()}  # Deduplicate input

                for tag_name in tag_list:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    post.tags.add(tag)

            # Handle tagged authors from hidden input (populated by JavaScript)
            tagged_author_ids = request.POST.get("tagged_author_ids", "").strip()
            if tagged_author_ids:
                author_ids = [int(id.strip()) for id in tagged_author_ids.split(",") if id.strip().isdigit()]
                tagged_authors = User.objects.filter(id__in=author_ids)
                post.tagged_authors.set(tagged_authors)

            return redirect("post_detail", post.id)
    else:
        form = PostForm()

    return render(request, "blog/create_post.html", {"form": form})


from .models import Comment, PostView, UserAnalytics, DailyAnalytics, PostLike
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Manually track the view
    user = request.user if request.user.is_authenticated else None
    ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    # Check if this user/IP has viewed this post in the last hour
    from django.utils import timezone
    from datetime import timedelta

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
        print(f"View tracked for post: {post.title}")

    # Get only top-level comments (not replies)
    comments = post.comments.filter(parent=None).order_by('created_at')

    # Split content into paragraphs at line breaks and capitalize first letters
    formatted_content = [p.strip().capitalize() for p in post.content.split("\n") if p.strip()]

    if request.method == "POST":
        if request.user.is_authenticated:
            text = request.POST.get("comment")
            parent_id = request.POST.get("parent_id")

            # Create comment or reply
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                Comment.objects.create(post=post, user=request.user, text=text, parent=parent_comment)
            else:
                Comment.objects.create(post=post, user=request.user, text=text)

            return redirect("post_detail", post_id=post.id)

    return render(request, "blog/post_detail.html", {
        "post": post,
        "comments": comments,
        "formatted_content": formatted_content
    })


from django.http import JsonResponse

@login_required
def search_users(request):
    """AJAX endpoint for user search autocomplete"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:  # Require at least 2 characters
        return JsonResponse({'users': []})

    # Search users by username, first_name, or last_name
    users = User.objects.filter(
        models.Q(username__icontains=query) |
        models.Q(first_name__icontains=query) |
        models.Q(last_name__icontains=query)
    ).exclude(id=request.user.id)[:10]  # Exclude current user, limit to 10 results

    user_data = []
    for user in users:
        full_name = f"{user.first_name} {user.last_name}".strip()
        display_name = f"{user.username}" + (f" ({full_name})" if full_name else "")

        user_data.append({
            'id': user.id,
            'username': user.username,
            'display_name': display_name,
            'profile_picture': user.profile.profile_picture.url if hasattr(user, 'profile') and user.profile.profile_picture else None
        })

    return JsonResponse({'users': user_data})

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Check if user already liked the post using PostLike model
    post_like, created = PostLike.objects.get_or_create(post=post, user=request.user)

    if not created:
        # User already liked, so unlike
        post_like.delete()
        post.likes.remove(request.user)
        liked = False
    else:
        # New like
        post.likes.add(request.user)
        liked = True

    return JsonResponse({"liked": liked, "total_likes": post.total_likes()})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post_id = comment.post.id

    # Check if user can delete the comment (comment owner or post owner)
    if request.user == comment.user or request.user == comment.post.author:
        comment.delete()

    return redirect("post_detail", post_id=post_id)

from django.shortcuts import render, get_object_or_404, redirect
from .models import Post
from .forms import PostForm

def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect("post_detail", post_id=post.id)  # Prevent unauthorized editing

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            # Save the post but don't commit to handle tags manually
            updated_post = form.save(commit=False)
            updated_post.save()

            # Clear existing tags first to avoid duplicates
            updated_post.tags.clear()

            # Handle existing tags from form
            selected_tags = form.cleaned_data.get("tags")
            if selected_tags:
                updated_post.tags.set(selected_tags)

            # Process new tags without duplicates
            new_tag_names = request.POST.get("new_tags", "").strip()
            if new_tag_names:
                tag_list = {tag.strip() for tag in new_tag_names.split(",") if tag.strip()}  # Deduplicate input

                for tag_name in tag_list:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    updated_post.tags.add(tag)

            # Handle tagged authors from hidden input (populated by JavaScript)
            tagged_author_ids = request.POST.get("tagged_author_ids", "").strip()
            if tagged_author_ids:
                author_ids = [int(id.strip()) for id in tagged_author_ids.split(",") if id.strip().isdigit()]
                tagged_authors = User.objects.filter(id__in=author_ids)
                updated_post.tagged_authors.set(tagged_authors)
            else:
                updated_post.tagged_authors.clear()

            return redirect("post_detail", post_id=post.id)
    else:
        # Pre-populate the new_tags field with existing tags that aren't in the dropdown
        existing_tag_names = [tag.name for tag in post.tags.all()]
        form = PostForm(instance=post)
        # You could add logic here to separate existing tags from new ones if needed

    return render(request, "blog/edit_post.html", {"form": form, "post": post})


def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user == post.author:
        post.delete()
        return redirect("home")  # Redirect to homepage after deletion

    return redirect("post_detail", post_id=post.id)  # Prevent unauthorized deletion

from .models import User, Profile, Post

@login_required
def author_profile(request, username):
    author = get_object_or_404(User, username=username)
    own_posts = Post.objects.filter(author=author).order_by("-created_at")
    tagged_posts = Post.objects.filter(tagged_authors=author).order_by("-created_at")

    is_own_profile = request.user == author  # Check if it's the authenticated user's profile

    # Pagination: Show first 6 posts for each category
    initial_own_posts = own_posts[:6]
    initial_tagged_posts = tagged_posts[:6]

    has_more_own = own_posts.count() > 6
    has_more_tagged = tagged_posts.count() > 6

    return render(request, "blog/author_profile.html", {
        "author": author,
        "own_posts": initial_own_posts,
        "tagged_posts": initial_tagged_posts,
        "is_own_profile": is_own_profile,
        "has_more_own": has_more_own,
        "has_more_tagged": has_more_tagged,
        "total_own_posts": own_posts.count(),
        "total_tagged_posts": tagged_posts.count(),
    })


from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect


from .forms import UserUpdateForm, ProfileUpdateForm

@login_required
def edit_profile(request):
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("author_profile", username=request.user.username)
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, "blog/edit_profile.html", context)


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect("profile", username=request.user.username)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "blog/change_password.html", {"form": form})


@login_required
def dashboard(request):
    """User dashboard with analytics and statistics."""
    user = request.user

    # Get or create user analytics and always update for real-time data
    analytics, created = UserAnalytics.objects.get_or_create(user=user)
    analytics.update_analytics()

    # Get user's posts
    user_posts = Post.objects.filter(author=user).order_by('-created_at')

    # Calculate date ranges
    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)

    # Get recent analytics data
    recent_views = PostView.objects.filter(
        post__author=user,
        viewed_at__date__gte=last_7_days
    ).count()

    # Get recent likes using PostLike model with timestamps
    recent_likes = PostLike.objects.filter(
        post__author=user,
        created_at__date__gte=last_7_days
    ).count()

    recent_comments = 0
    for post in user_posts:
        recent_comments += post.comments.filter(
            created_at__date__gte=last_7_days
        ).count()

    # Get top performing posts
    top_posts = []
    for post in user_posts[:10]:  # Limit to recent posts
        views_count = post.views.count()
        likes_count = post.total_likes()
        comments_count = post.comments.count()

        top_posts.append({
            'post': post,
            'views': views_count,
            'likes': likes_count,
            'comments': comments_count,
            'engagement': views_count + likes_count * 2 + comments_count * 3
        })

    # Sort by engagement score
    top_posts.sort(key=lambda x: x['engagement'], reverse=True)
    top_posts = top_posts[:5]  # Top 5 posts

    # Get daily analytics for the last 7 days
    daily_data = []
    for i in range(7):
        date = today - timedelta(days=i)
        day_views = PostView.objects.filter(
            post__author=user,
            viewed_at__date=date
        ).count()

        # Get likes for this specific date using PostLike model
        day_likes = PostLike.objects.filter(
            post__author=user,
            created_at__date=date
        ).count()

        day_comments = 0
        for post in user_posts:
            day_comments += post.comments.filter(
                created_at__date=date
            ).count()

        daily_data.append({
            'date': date,
            'views': day_views,
            'likes': day_likes,
            'comments': day_comments
        })

    daily_data.reverse()  # Show oldest to newest

    # Get visitor data
    visitor_data = PostView.objects.filter(
        post__author=user
    ).values('ip_address').annotate(
        views=Count('id')
    ).order_by('-views')[:10]

    context = {
        'analytics': analytics,
        'user_posts': user_posts,
        'recent_views': recent_views,
        'recent_likes': recent_likes,
        'recent_comments': recent_comments,
        'top_posts': top_posts,
        'daily_data': daily_data,
        'visitor_data': visitor_data,
        'total_posts': user_posts.count(),
    }

    return render(request, "blog/dashboard.html", context)


from .forms import CustomUserCreationForm 

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(
                user=user,
                bio=form.cleaned_data["bio"],
                profile_picture=form.cleaned_data["profile_picture"]
            )
            return redirect("login")  # Redirect to login after signup
    else:
        form = CustomUserCreationForm()

    return render(request, "blog/register.html", {"form": form})

# blog/views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import LoginForm

def custom_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
        else:
            return render(request, "blog/login.html", {"form": form, "error": "Invalid username or password"})
    else:
        form = LoginForm()
    return render(request, "blog/login.html", {"form": form})


from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect("home")  # Redirect to login page after logout


from django.http import JsonResponse
from django.contrib.auth.models import User

def search_authors(request):
    query = request.GET.get("q", "")
    if query:
        authors = User.objects.filter(username__icontains=query)[:5].values("username")
        return JsonResponse({"authors": list(authors)})
    return JsonResponse({"authors": []})

from django.http import JsonResponse
from .models import Tag

def search_tags(request):
    query = request.GET.get("q", "")
    if query:
        tags = Tag.objects.filter(name__icontains=query).values("name")[:5]
        return JsonResponse({"tags": list(tags)})
    return JsonResponse({"tags": []})

