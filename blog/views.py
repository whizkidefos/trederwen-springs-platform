from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import BlogPost, BlogCategory, BlogTag
from core.models import SiteSettings

def blog_list(request):
    """Display all blog posts with filtering options"""
    # Get all published blog posts
    posts = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now()
    ).select_related('category', 'author').order_by('-published_at')
    
    # Handle category filtering
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(BlogCategory, slug=category_slug)
        posts = posts.filter(category=category)
    else:
        category = None
    
    # Handle tag filtering
    tag_slug = request.GET.get('tag')
    if tag_slug:
        tag = get_object_or_404(BlogTag, slug=tag_slug)
        posts = posts.filter(tags=tag)
    else:
        tag = None
    
    # Handle search query
    query = request.GET.get('q')
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(posts, 9)  # 9 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for sidebar
    categories = BlogCategory.objects.all()
    
    # Get popular tags
    tags = BlogTag.objects.all()[:15]
    
    # Get featured posts
    featured_posts = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now(),
        is_featured=True
    ).select_related('category', 'author')[:3]
    
    # Get site settings
    settings = SiteSettings.get_settings()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'tags': tags,
        'featured_posts': featured_posts,
        'current_category': category,
        'current_tag': tag,
        'query': query,
        'settings': settings,
    }
    
    return render(request, 'blog/blog_list.html', context)

def blog_detail(request, slug):
    """Display a single blog post"""
    post = get_object_or_404(
        BlogPost,
        slug=slug,
        status='published',
        published_at__lte=timezone.now()
    )
    
    # Increment view count
    post.view_count += 1
    post.save(update_fields=['view_count'])
    
    # Get related posts
    related_posts = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now(),
        category=post.category
    ).exclude(id=post.id).select_related('category', 'author')[:3]
    
    # Get site settings
    settings = SiteSettings.get_settings()
    
    context = {
        'post': post,
        'related_posts': related_posts,
        'settings': settings,
    }
    
    return render(request, 'blog/blog_detail.html', context)

def blog_category(request, slug):
    """Display posts in a specific category"""
    category = get_object_or_404(BlogCategory, slug=slug)
    
    posts = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now(),
        category=category
    ).select_related('category', 'author').order_by('-published_at')
    
    # Pagination
    paginator = Paginator(posts, 9)  # 9 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for sidebar
    categories = BlogCategory.objects.all()
    
    # Get popular tags
    tags = BlogTag.objects.all()[:15]
    
    # Get site settings
    settings = SiteSettings.get_settings()
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'categories': categories,
        'tags': tags,
        'settings': settings,
    }
    
    return render(request, 'blog/blog_category.html', context)

def blog_tag(request, slug):
    """Display posts with a specific tag"""
    tag = get_object_or_404(BlogTag, slug=slug)
    
    posts = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now(),
        tags=tag
    ).select_related('category', 'author').order_by('-published_at')
    
    # Pagination
    paginator = Paginator(posts, 9)  # 9 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for sidebar
    categories = BlogCategory.objects.all()
    
    # Get popular tags
    tags = BlogTag.objects.all()[:15]
    
    # Get site settings
    settings = SiteSettings.get_settings()
    
    context = {
        'tag': tag,
        'page_obj': page_obj,
        'categories': categories,
        'tags': tags,
        'settings': settings,
    }
    
    return render(request, 'blog/blog_tag.html', context)
