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

    if request.method == "POST":
        if request.user.is_authenticated:
            text = request.POST.get("comment")
            Comment.objects.create(post=post, user=request.user, text=text)
            return redirect("post_detail", post_id=post.id)

    return render(request, "blog/post_detail.html", {"post": post, "comments": comments})

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

from django.contrib.auth.models import User

def author_profile(request, username):
    author = get_object_or_404(User, username=username)
    own_posts = Post.objects.filter(author=author)
    tagged_posts = Post.objects.filter(tagged_authors=author)

    return render(request, "blog/author_profile.html", {
        "author": author,
        "own_posts": own_posts,
        "tagged_posts": tagged_posts
    })

from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from .models import Profile

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

