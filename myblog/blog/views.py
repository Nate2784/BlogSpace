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

            messages.success(request, f"🎉 Your post '{post.title}' has been published successfully!")
            return redirect("post_detail", post.id)
        else:
            messages.error(request, "Please correct the errors below and try again.")
    else:
        form = PostForm()

    return render(request, "blog/create_post.html", {"form": form})


from .models import Comment, PostView, UserAnalytics, DailyAnalytics, PostLike
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # View tracking is handled by middleware, no need to duplicate here

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
        messages.error(request, "You don't have permission to edit this post.")
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

            messages.success(request, f"✏️ Your post '{updated_post.title}' has been updated successfully!")
            return redirect("post_detail", post_id=post.id)
        else:
            messages.error(request, "Please correct the errors below and try again.")
    else:
        # Pre-populate the new_tags field with existing tags that aren't in the dropdown
        existing_tag_names = [tag.name for tag in post.tags.all()]
        form = PostForm(instance=post)
        # You could add logic here to separate existing tags from new ones if needed

    return render(request, "blog/edit_post.html", {"form": form, "post": post})


def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user == post.author:
        post_title = post.title
        post.delete()
        messages.success(request, f"🗑️ Your post '{post_title}' has been deleted successfully.")
        return redirect("home")  # Redirect to homepage after deletion
    else:
        messages.error(request, "You don't have permission to delete this post.")

    return redirect("post_detail", post_id=post.id)  # Prevent unauthorized deletion

from .models import User, Profile, Post

@login_required
def author_profile(request, username):
    author = get_object_or_404(User, username=username)
    own_posts = Post.objects.filter(author=author).order_by("-created_at")
    tagged_posts = Post.objects.filter(tagged_authors=author).order_by("-created_at")

    is_own_profile = request.user == author  # Check if it's the authenticated user's profile

    # Calculate total likes for author's posts
    total_likes = sum(post.likes.count() for post in own_posts)

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
        "total_likes": total_likes,
    })


@login_required
def load_more_own_posts(request, username):
    """AJAX view to load more own posts for author profile."""
    author = get_object_or_404(User, username=username)
    offset = int(request.GET.get('offset', 0))
    limit = 6

    own_posts = Post.objects.filter(author=author).order_by("-created_at")[offset:offset + limit]
    has_more = Post.objects.filter(author=author).count() > offset + limit

    # Render posts HTML
    posts_html = ""
    for post in own_posts:
        posts_html += f'''
        <div class="col-lg-6 mb-4">
          <div class="card h-100 shadow-sm border-0" style="border-radius: 15px; overflow: hidden;">
            {"<img src='" + post.image.url + "' class='card-img-top' alt='" + post.title + "' style='height: 200px; object-fit: cover;'>" if post.image else ""}
            <div class="card-body d-flex flex-column">
              <h5 class="card-title">
                <a href="/post/{post.id}/" class="text-decoration-none text-dark">
                  {post.title}
                </a>
              </h5>
              <p class="card-text text-muted">{post.content[:100]}...</p>

              <div class="post-stats mb-2">
                <span class="badge bg-light text-dark me-2">
                  <i class="fas fa-heart text-danger me-1"></i>{post.likes.count()}
                </span>
                <span class="badge bg-light text-dark me-2">
                  <i class="fas fa-comment text-primary me-1"></i>{post.comments.count()}
                </span>
                <span class="badge bg-light text-dark">
                  <i class="fas fa-eye text-info me-1"></i>{post.views.count()}
                </span>
              </div>

              <div class="mt-auto">
                <div class="d-flex justify-content-between align-items-center">
                  <small class="text-muted">{post.created_at.strftime("%b %d, %Y")}</small>
                  <a href="/post/{post.id}/" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-eye me-1"></i>View
                  </a>
                </div>
                {"<div class='mt-2'><a href='/post/" + str(post.id) + "/edit/' class='btn btn-outline-warning btn-sm me-2'><i class='fas fa-edit me-1'></i>Edit</a><button class='btn btn-outline-danger btn-sm' onclick='confirmDelete(" + str(post.id) + ")'><i class='fas fa-trash me-1'></i>Delete</button></div>" if request.user == author else ""}
              </div>
            </div>
          </div>
        </div>
        '''

    return JsonResponse({
        'success': True,
        'html': posts_html,
        'has_more': has_more
    })


@login_required
def load_more_tagged_posts(request, username):
    """AJAX view to load more tagged posts for author profile."""
    author = get_object_or_404(User, username=username)
    offset = int(request.GET.get('offset', 0))
    limit = 6

    tagged_posts = Post.objects.filter(tagged_authors=author).order_by("-created_at")[offset:offset + limit]
    has_more = Post.objects.filter(tagged_authors=author).count() > offset + limit

    # Render posts HTML
    posts_html = ""
    for post in tagged_posts:
        posts_html += f'''
        <div class="col-lg-6 mb-4">
          <div class="card h-100 shadow-sm border-0" style="border-radius: 15px; overflow: hidden;">
            {"<img src='" + post.image.url + "' class='card-img-top' alt='" + post.title + "' style='height: 200px; object-fit: cover;'>" if post.image else ""}
            <div class="card-body d-flex flex-column">
              <h5 class="card-title">
                <a href="/post/{post.id}/" class="text-decoration-none text-dark">
                  {post.title}
                </a>
              </h5>
              <p class="card-text text-muted">{post.content[:100]}...</p>

              <div class="post-stats mb-2">
                <span class="badge bg-light text-dark me-2">
                  <i class="fas fa-heart text-danger me-1"></i>{post.likes.count()}
                </span>
                <span class="badge bg-light text-dark me-2">
                  <i class="fas fa-comment text-primary me-1"></i>{post.comments.count()}
                </span>
                <span class="badge bg-light text-dark">
                  <i class="fas fa-eye text-info me-1"></i>{post.views.count()}
                </span>
              </div>

              <div class="mt-auto">
                <div class="d-flex justify-content-between align-items-center">
                  <small class="text-muted">By {post.author.username} on {post.created_at.strftime("%b %d, %Y")}</small>
                  <a href="/post/{post.id}/" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-eye me-1"></i>View
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
        '''

    return JsonResponse({
        'success': True,
        'html': posts_html,
        'has_more': has_more
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


from .forms import CustomUserCreationForm, EmailVerificationForm, PasswordResetRequestForm, PasswordResetVerifyForm, PasswordResetConfirmForm
from .models import EmailVerification, PasswordResetToken
from .utils import send_verification_email, send_welcome_email, send_password_reset_email, send_password_reset_success_email
from django.contrib import messages

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                print("🔄 Starting user registration process...")

                # Save user as inactive
                print("📝 Saving user...")
                user = form.save()
                print(f"✅ User created: {user.username} ({user.email})")

                # Create profile
                print("👤 Creating user profile...")
                Profile.objects.create(
                    user=user,
                    bio=form.cleaned_data.get("bio", ""),
                    profile_picture=form.cleaned_data.get("profile_picture")
                )
                print("✅ Profile created successfully")

                # Create or get email verification record and generate OTP
                print("🔑 Creating email verification...")
                email_verification, created = EmailVerification.objects.get_or_create(user=user)
                print(f"✅ Email verification {'created' if created else 'retrieved'}")

                print("🎲 Generating OTP...")
                otp_code = email_verification.generate_otp()
                print(f"✅ OTP generated: {otp_code}")

                # Send verification email
                print("📧 Sending verification email...")
                email_sent = send_verification_email(user, otp_code)

                if email_sent:
                    print("✅ Verification email sent successfully")
                    messages.success(
                        request,
                        f"Registration successful! A verification code has been sent to {user.email}. "
                        "Please check your email and enter the code to activate your account."
                    )
                else:
                    print("⚠️ Email sending failed, but proceeding with registration")
                    messages.warning(
                        request,
                        f"Registration successful! However, we couldn't send the verification email to {user.email}. "
                        f"Your verification code is: {otp_code}. Please enter this code to activate your account."
                    )

                # Store user ID in session for verification regardless of email status
                request.session['pending_verification_user_id'] = user.id
                request.session.save()  # Explicitly save session
                print(f"🔗 Stored user ID in session: {user.id}")
                print(f"🔗 Session data: {dict(request.session)}")

                # Also add user_id as URL parameter as backup
                from django.urls import reverse
                verify_url = reverse("verify_email") + f"?user_id={user.id}"
                print(f"🔗 Redirecting to: {verify_url}")
                return redirect(verify_url)

            except Exception as e:
                # Log the actual error for debugging
                print(f"❌ Registration error: {str(e)}")
                import traceback
                traceback.print_exc()

                # Clean up any partially created user if something went wrong
                try:
                    if 'user' in locals():
                        print(f"🧹 Cleaning up user: {user.username}")
                        user.delete()
                        print("✅ User cleanup completed")
                except Exception as cleanup_error:
                    print(f"⚠️ Cleanup error: {cleanup_error}")

                # Provide specific error messages based on the error type
                if "UNIQUE constraint failed" in str(e) or "already exists" in str(e):
                    messages.error(
                        request,
                        "An account with this email or username already exists. Please try logging in instead."
                    )
                elif "email" in str(e).lower():
                    messages.error(
                        request,
                        "There was an issue with the email address. Please check and try again."
                    )
                else:
                    messages.error(
                        request,
                        "Registration failed due to a technical issue. Please try again or contact support if the problem persists."
                    )
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(request, "blog/register.html", {"form": form})


def verify_email(request):
    """Handle email verification with OTP."""
    print(f"🔍 Verify email view accessed")
    print(f"🔍 Session data: {dict(request.session)}")

    # Check if user has pending verification (from session or URL parameter)
    user_id = request.session.get('pending_verification_user_id') or request.GET.get('user_id')
    print(f"🔍 User ID from session: {request.session.get('pending_verification_user_id')}")
    print(f"🔍 User ID from URL: {request.GET.get('user_id')}")
    print(f"🔍 Final user ID: {user_id}")

    if not user_id:
        print("❌ No user ID in session or URL")
        messages.error(request, "No pending email verification found. Please register first.")
        return redirect("register")

    try:
        # First, try to get the user (regardless of active status)
        print(f"🔍 Looking for user with ID: {user_id}")
        user = User.objects.get(id=user_id)
        print(f"✅ Found user: {user.username} (active: {user.is_active})")

        # Check if user is already active (already verified)
        if user.is_active:
            print(f"✅ User {user.username} is already verified")
            # User is already verified, redirect to login
            messages.success(request, "Your account is already verified. You can log in now.")
            # Clear session
            if 'pending_verification_user_id' in request.session:
                del request.session['pending_verification_user_id']
            return redirect("login")

        # User exists but not active, get email verification
        print(f"🔍 Looking for email verification for user: {user.username}")
        email_verification = EmailVerification.objects.get(user=user)
        print(f"✅ Found email verification record")

    except User.DoesNotExist:
        messages.error(request, "Invalid verification session. Please register again.")
        return redirect("register")
    except EmailVerification.DoesNotExist:
        # User exists but no email verification record - create one
        email_verification = EmailVerification.objects.create(user=user)
        otp_code = email_verification.generate_otp()
        messages.info(request, f"New verification code generated: {otp_code}")
        print(f"🔄 Created new email verification for existing user: {user.username}")

    if request.method == "POST":
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp_code']
            success, message = email_verification.verify_otp(entered_otp)

            if success:
                # Send welcome email
                send_welcome_email(user)

                # Clear session
                del request.session['pending_verification_user_id']

                messages.success(request, message + " You can now log in to your account.")
                return redirect("login")
            else:
                messages.error(request, message)
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = EmailVerificationForm()

    # Check if OTP is expired
    if email_verification.is_expired():
        messages.warning(
            request,
            "Your verification code has expired. Click 'Resend Code' to get a new one."
        )

    context = {
        'form': form,
        'user_email': user.email,
        'masked_email': f"{user.email[:2]}***@{user.email.split('@')[1]}"
    }
    return render(request, "blog/verify_email.html", context)


def resend_verification_code(request):
    """Resend verification code to user."""
    user_id = request.session.get('pending_verification_user_id')
    if not user_id:
        messages.error(request, "No pending email verification found.")
        return redirect("register")

    try:
        user = User.objects.get(id=user_id, is_active=False)
        email_verification = EmailVerification.objects.get(user=user)

        # Generate new OTP
        otp_code = email_verification.generate_otp()

        # Send verification email
        if send_verification_email(user, otp_code):
            messages.success(request, "A new verification code has been sent to your email.")
        else:
            messages.error(request, "Failed to send verification email. Please try again.")

    except (User.DoesNotExist, EmailVerification.DoesNotExist):
        messages.error(request, "Invalid verification session.")
        return redirect("register")

    return redirect("verify_email")


def password_reset_request(request):
    """Handle password reset request."""
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email, is_active=True)

                # Create or get existing password reset token
                reset_token, created = PasswordResetToken.objects.get_or_create(
                    user=user,
                    is_used=False,
                    defaults={'otp_code': ''}
                )

                # Generate new OTP
                otp_code = reset_token.generate_otp()

                # Send password reset email
                if send_password_reset_email(user, otp_code):
                    messages.success(
                        request,
                        f"Password reset code has been sent to {email}. Please check your email."
                    )
                    # Store user ID in session for verification
                    request.session['password_reset_user_id'] = user.id
                    return redirect("password_reset_verify")
                else:
                    messages.error(
                        request,
                        "Failed to send password reset email. Please try again."
                    )

            except User.DoesNotExist:
                # Don't reveal that the user doesn't exist
                messages.success(
                    request,
                    f"If an account with {email} exists, a password reset code has been sent."
                )
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = PasswordResetRequestForm()

    return render(request, "blog/password_reset_request.html", {"form": form})


def password_reset_verify(request):
    """Handle password reset OTP verification."""
    # Check if user has pending password reset
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        messages.error(request, "No pending password reset found. Please request a new reset.")
        return redirect("password_reset_request")

    try:
        user = User.objects.get(id=user_id, is_active=True)
        reset_token = PasswordResetToken.objects.filter(user=user, is_used=False).first()

        if not reset_token:
            messages.error(request, "No valid reset token found. Please request a new reset.")
            return redirect("password_reset_request")

    except User.DoesNotExist:
        messages.error(request, "Invalid reset session. Please request a new reset.")
        return redirect("password_reset_request")

    if request.method == "POST":
        form = PasswordResetVerifyForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp_code']
            success, message = reset_token.verify_otp(entered_otp)

            if success:
                # Store verified token ID in session
                request.session['verified_reset_token_id'] = reset_token.id
                messages.success(request, message + " You can now set a new password.")
                return redirect("password_reset_confirm")
            else:
                messages.error(request, message)
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = PasswordResetVerifyForm()

    # Check if OTP is expired
    if reset_token.is_expired():
        messages.warning(
            request,
            "Your reset code has expired. Click 'Resend Code' to get a new one."
        )

    context = {
        'form': form,
        'user_email': user.email,
        'masked_email': f"{user.email[:2]}***@{user.email.split('@')[1]}"
    }
    return render(request, "blog/password_reset_verify.html", context)


def password_reset_confirm(request):
    """Handle new password setting after OTP verification."""
    # Check if user has verified reset token
    token_id = request.session.get('verified_reset_token_id')
    if not token_id:
        messages.error(request, "No verified reset session found. Please start the reset process again.")
        return redirect("password_reset_request")

    try:
        reset_token = PasswordResetToken.objects.get(id=token_id, is_used=False)
        user = reset_token.user
    except PasswordResetToken.DoesNotExist:
        messages.error(request, "Invalid reset session. Please start the reset process again.")
        return redirect("password_reset_request")

    if request.method == "POST":
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']

            # Set new password
            user.set_password(new_password)
            user.save()

            # Mark token as used
            reset_token.mark_as_used()

            # Clear session data
            if 'password_reset_user_id' in request.session:
                del request.session['password_reset_user_id']
            if 'verified_reset_token_id' in request.session:
                del request.session['verified_reset_token_id']

            # Send success email
            send_password_reset_success_email(user)

            messages.success(
                request,
                "Your password has been reset successfully! You can now log in with your new password."
            )
            return redirect("login")
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = PasswordResetConfirmForm()

    context = {
        'form': form,
        'user_email': user.email
    }
    return render(request, "blog/password_reset_confirm.html", context)


def resend_password_reset_code(request):
    """Resend password reset code to user."""
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        messages.error(request, "No pending password reset found.")
        return redirect("password_reset_request")

    try:
        user = User.objects.get(id=user_id, is_active=True)
        reset_token = PasswordResetToken.objects.filter(user=user, is_used=False).first()

        if not reset_token:
            # Create new token if none exists
            reset_token = PasswordResetToken.objects.create(user=user)

        # Generate new OTP
        otp_code = reset_token.generate_otp()

        # Send password reset email
        if send_password_reset_email(user, otp_code):
            messages.success(request, "A new password reset code has been sent to your email.")
        else:
            messages.error(request, "Failed to send password reset email. Please try again.")

    except User.DoesNotExist:
        messages.error(request, "Invalid reset session.")
        return redirect("password_reset_request")

    return redirect("password_reset_verify")


# blog/views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import LoginForm

def custom_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # Check if user account is active
            if not user.is_active:
                # Check if user has pending email verification
                try:
                    email_verification = EmailVerification.objects.get(user=user)
                    if not email_verification.is_verified:
                        messages.error(
                            request,
                            "Your account is not yet verified. Please check your email for the verification code."
                        )
                        # Set session for verification
                        request.session['pending_verification_user_id'] = user.id
                        return redirect("verify_email")
                    else:
                        messages.error(request, "Your account has been deactivated. Please contact support.")
                except EmailVerification.DoesNotExist:
                    messages.error(request, "Your account is not active. Please contact support.")

                return render(request, "blog/login.html", {"form": form})

            # User is active, proceed with login
            login(request, user)
            # Clear any existing messages before adding welcome message
            storage = messages.get_messages(request)
            for _ in storage:
                pass  # This clears the messages
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect("home")
        else:
            # Check if the error is due to inactive account
            username = request.POST.get('username')
            if username:
                try:
                    user = User.objects.get(username=username)
                    if not user.is_active:
                        messages.error(
                            request,
                            "Your account is not yet verified. Please check your email for the verification code."
                        )
                        request.session['pending_verification_user_id'] = user.id
                        return redirect("verify_email")
                except User.DoesNotExist:
                    pass

            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, "blog/login.html", {"form": form})
    else:
        form = LoginForm()
    return render(request, "blog/login.html", {"form": form})


from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    if request.user.is_authenticated:
        username = request.user.first_name or request.user.username
        logout(request)
        messages.success(request, f"You have been successfully logged out. See you soon, {username}!")
    else:
        messages.info(request, "You were not logged in.")

    return redirect("login")  # Redirect to login page after logout


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

