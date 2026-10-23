from django.shortcuts import render
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .forms import CustomUserCreationForm, PostForm, CommentForm, ProfileEditForm
from .models import Category, Post, Comment
from django.http import Http404

User = get_user_model()

def filter_published_posts(queryset):
    return queryset.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    )

def index(request):
    template = 'blog/index.html'
    post_list = filter_published_posts(
        Post.objects.select_related('category', 'location', 'author')
    )
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    
    post_list = filter_published_posts(
        category.posts.select_related('location', 'author')
    )
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'blog/detail.html'
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        pk=post_id,
    )
    
    is_visible_to_all = (
        post.is_published 
        and post.category.is_published 
        and post.pub_date <= timezone.now()
    )
    
    if not is_visible_to_all and request.user != post.author:
        raise Http404("Пост не найден")
        
    comments = post.comments.select_related('author').all()
    form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


def registration(request):
    form = CustomUserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('login')
    return render(request, 'registration/registration_form.html', {'form': form})


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    
    posts = profile_user.author_posts.all()
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile': profile_user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)

@login_required
def edit_profile(request):
    user = request.user
    
    form = ProfileEditForm(request.POST or None, instance=user)
    
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=user.username)
        
    return render(request, 'blog/user.html', {'form': form}) 

@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.id)
        
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post.id)
        
    return render(request, 'blog/create.html', {'form': form})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.id)
        
    form = PostForm(instance=post)
    
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
        
    return render(request, 'blog/create.html', {'form': form})

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
        
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
        
    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
        
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
        
    return render(request, 'blog/comment.html', {'comment': comment})
