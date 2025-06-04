"""
URL configuration for myblog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from blog.views import *
from django.contrib.auth.views import LoginView,LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home, name="home"),

    path("posts/", posts, name="posts_page"),
    path("create-post/", create_post, name="create_post"),
    path("post/<int:post_id>/", post_detail, name="post_detail"),
    path("post/<int:post_id>/like/", like_post, name="like_post"),

    path("profile/<str:username>/", author_profile, name="author_profile"),

    path("register/", register, name="register"),
    path("login/", custom_login, name="login"),
    path("logout/", custom_logout, name="logout"),

    path("search-authors/", search_authors, name="search_authors"),
    path("search-tags/", search_tags, name="search_tags"),
]

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
