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
    path("posts/load-more/", load_more_posts, name="load_more_posts"),
    path("author/<str:username>/load-more/", load_more_author_posts, name="load_more_author_posts"),
    path("create-post/", create_post, name="create_post"),
    path("post/<int:post_id>/", post_detail, name="post_detail"),
    path("post/<int:post_id>/like/", like_post, name="like_post"),
    path("post/<int:post_id>/edit/", edit_post, name="edit_post"),
    path("post/<int:post_id>/delete/", delete_post, name="delete_post"),
    path("comment/<int:comment_id>/delete/", delete_comment, name="delete_comment"),

    path('dashboard/', dashboard, name='dashboard'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('profile/change-password/', change_password, name='change_password'),
    path('profile/<str:username>/', author_profile, name='author_profile'),
    path('profile/<str:username>/load-more-own/', load_more_own_posts, name='load_more_own_posts'),
    path('profile/<str:username>/load-more-tagged/', load_more_tagged_posts, name='load_more_tagged_posts'),

    path("register/", register, name="register"),
    path("verify-email/", verify_email, name="verify_email"),
    path("resend-verification/", resend_verification_code, name="resend_verification"),
    path("login/", custom_login, name="login"),
    path("logout/", custom_logout, name="logout"),

    # Password Reset URLs
    path("password-reset/", password_reset_request, name="password_reset_request"),
    path("password-reset/verify/", password_reset_verify, name="password_reset_verify"),
    path("password-reset/confirm/", password_reset_confirm, name="password_reset_confirm"),
    path("password-reset/resend/", resend_password_reset_code, name="resend_password_reset"),

    path("search-authors/", search_authors, name="search_authors"),
    path("search-tags/", search_tags, name="search_tags"),
    path("api/search-users/", search_users, name="search_users"),
]

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
