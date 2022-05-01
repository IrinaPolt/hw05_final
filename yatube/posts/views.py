from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from .models import User, Post, Group, Follow, get_user_model
from .forms import PostForm, CommentForm

PAGE_NMB = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    paginator = Paginator(post_list, PAGE_NMB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'post_list': post_list,
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_list(request):
    return render(request, 'posts/group_list.html')


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().order_by('-pub_date')
    paginator = Paginator(posts, PAGE_NMB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'group': group,
        'posts': posts,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_user_model()
    user = get_object_or_404(author, username=username)
    posts = user.posts.all()
    posts_count = posts.count()
    paginator = Paginator(posts, PAGE_NMB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=user).exists()
    else:
        following = False
    context = {
        'author': user,
        'posts': posts,
        'page_obj': page_obj,
        'posts_count': posts_count,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    queryset = Post.objects.select_related('author', 'group')
    post = get_object_or_404(queryset, id=post_id)
    author_posts = post.author.posts.count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'author_posts': author_posts,
        'form': form,
        'post_id': post_id,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None,
                        files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post = form.save()
            return redirect('posts:profile',
                            username=post.author)
        return render(request, 'posts/create_post.html',
                      {'form': form})
    else:
        form = PostForm(request.POST or None,
                        files=request.FILES or None)
        return render(request, 'posts/create_post.html',
                      {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    else:
        request.method == 'POST'
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post)
        if not form.is_valid():
            return render(request, 'posts/create_post.html',
                          {'form': form, 'is_edit': is_edit, 'post': post})
        else:
            post.save()
            return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, PAGE_NMB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follows = Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
