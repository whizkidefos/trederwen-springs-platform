from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Product, Category, Brand, ProductTag
from ai_recommendations.services import RecommendationService

def product_list(request):
    """Display all products with filtering options"""
    # Get all active products
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    
    # Handle category filtering
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(Q(category=category) | Q(category__parent=category))
    else:
        category = None
    
    # Handle brand filtering
    brand_slug = request.GET.get('brand')
    if brand_slug:
        brand = get_object_or_404(Brand, slug=brand_slug, is_active=True)
        products = products.filter(brand=brand)
    else:
        brand = None
    
    # Handle tag filtering
    tag_slug = request.GET.get('tag')
    if tag_slug:
        tag = get_object_or_404(ProductTag, slug=tag_slug)
        products = products.filter(tags=tag)
    else:
        tag = None
    
    # Handle sorting
    sort = request.GET.get('sort', 'default')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'popular':
        products = products.order_by('-view_count')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for sidebar
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    ).annotate(product_count=Count('products'))
    
    # Get all brands for sidebar
    brands = Brand.objects.filter(is_active=True).annotate(product_count=Count('products'))
    
    # Get popular tags
    tags = ProductTag.objects.annotate(product_count=Count('products')).order_by('-product_count')[:15]
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'brands': brands,
        'tags': tags,
        'current_category': category,
        'current_brand': brand,
        'current_tag': tag,
        'current_sort': sort,
        'total_products': paginator.count,
    }
    
    return render(request, 'products/product_list.html', context)

def product_detail(request, slug):
    """Display product details"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Increment view count
    product.increment_view_count()
    
    # Get product variants
    variants = product.variants.filter(is_active=True)
    
    # Get product reviews
    reviews = product.reviews.filter(is_approved=True).select_related('user')
    
    # Get similar products using AI recommendations
    similar_products = []
    try:
        recommendation_service = RecommendationService()
        similar_products = recommendation_service.get_similar_products(product, request)
    except Exception:
        # Fallback to simple category-based recommendations
        similar_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'variants': variants,
        'reviews': reviews,
        'similar_products': similar_products,
    }
    
    return render(request, 'products/product_detail.html', context)

def category_list(request):
    """Display all product categories"""
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    ).annotate(product_count=Count('products'))
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'products/category_list.html', context)

def category_detail(request, slug):
    """Display products in a specific category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get all products in this category and its subcategories
    products = Product.objects.filter(
        Q(category=category) | Q(category__parent=category),
        is_active=True
    ).select_related('category').prefetch_related('images')
    
    # Handle sorting
    sort = request.GET.get('sort', 'default')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'popular':
        products = products.order_by('-view_count')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get subcategories
    subcategories = category.children.filter(is_active=True).annotate(product_count=Count('products'))
    
    context = {
        'category': category,
        'subcategories': subcategories,
        'page_obj': page_obj,
        'current_sort': sort,
        'total_products': paginator.count,
    }
    
    return render(request, 'products/category_detail.html', context)
