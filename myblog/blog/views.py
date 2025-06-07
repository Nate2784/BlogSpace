from django.shortcuts import render, get_object_or_404
from .models import Post, Profile

def home(request):
    posts = Post.objects.all().order_by("-created_at")[:10]  # Show only the latest 10 posts

    return render(request, "blog/home.html", {"posts": posts})

from django.shortcuts import render
from django.db.models import Q
from .models import Post, Tag

def posts(request):
    query = request.GET.get("q")
    selected_tag = request.GET.get("tag")
    posts = Post.objects.all().order_by("-created_at")
    tags = Tag.objects.all()  # Get all available tags

    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(author__username__icontains=query))

    if selected_tag:
        posts = posts.filter(tags__name__icontains=selected_tag)

    return render(request, "blog/posts.html", {
        "posts": posts,
        "tags": tags,
        "query": query,
        "selected_tag": selected_tag
    })

from django.shortcuts import render, redirect
from .models import Post, Tag
from .forms import PostForm
from django.contrib.auth.decorators import login_required

@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            # Handling new tags creation
            new_tags = request.POST.get("new_tags")
            if new_tags:
                tag_names = [tag.strip() for tag in new_tags.split(",")]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    post.tags.add(tag)

            form.save_m2m()  # Save many-to-many relationships
            return redirect("post_detail", post.id)
    else:
        form = PostForm()

    return render(request, "blog/create_post.html", {"form": form})


from .models import  Comment

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()

    # Split content into paragraphs at line breaks and capitalize first letters
    formatted_content = [p.strip().capitalize() for p in post.content.split("\n") if p.strip()]

    if request.method == "POST":
        if request.user.is_authenticated:
            text = request.POST.get("comment")
            Comment.objects.create(post=post, user=request.user, text=text)
            return redirect("post_detail", post_id=post.id)

    return render(request, "blog/post_detail.html", {
        "post": post, 
        "comments": comments, 
        "formatted_content": formatted_content
    })


from django.http import JsonResponse

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    return JsonResponse({"liked": liked, "total_likes": post.total_likes()})

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
            form.save()
            return redirect("post_detail", post_id=post.id)
    else:
        form = PostForm(instance=post)

    return render(request, "blog/edit_post.html", {"form": form, "post": post})


def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user == post.author:
        post.delete()
        return redirect("home")  # Redirect to homepage after deletion

    return redirect("post_detail", post_id=post.id)  # Prevent unauthorized deletion

from .models import User, Profile, Post

def author_profile(request, username):
    author = get_object_or_404(User, username=username)
    own_posts = Post.objects.filter(author=author)
    tagged_posts = Post.objects.filter(tagged_authors=author)

    is_own_profile = request.user == author  # Check if it's the authenticated user's profile

    return render(request, "blog/author_profile.html", {
        "author": author,
        "own_posts": own_posts,
        "tagged_posts": tagged_posts,
        "is_own_profile": is_own_profile,
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

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm

def custom_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, request.POST)
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")  # Redirect to homepage after login
        else:
            return render(request, "blog/login.html", {"form": form, "error": "Invalid username or password"})
    else:
        form = AuthenticationForm()

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

