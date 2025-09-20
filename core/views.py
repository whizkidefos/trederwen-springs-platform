# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from products.models import Product, Category, ProductTag
from blog.models import BlogPost
from core.models import SiteSettings, Newsletter, ContactMessage, FAQ
from ai_recommendations.services import RecommendationService
import json

def home(request):
    """Homepage view"""
    # Get featured products
    featured_products = Product.objects.filter(
        is_active=True, 
        is_featured=True
    ).select_related('category').prefetch_related('images')[:8]
    
    # Get latest blog posts
    latest_posts = []
    try:
        from blog.models import BlogPost
        latest_posts = BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('category', 'author')[:3]
    except Exception:
        # Blog app might not be migrated yet
        pass
    
    # Get categories
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    ).annotate(product_count=Count('products'))[:6]
    
    # Get recommendations for user/session
    recommendations = []
    try:
        from ai_recommendations.services import RecommendationService
        recommendation_service = RecommendationService()
        recommendations = recommendation_service.get_homepage_recommendations(request)
    except Exception:
        # AI recommendations might not be ready yet
        pass
    
    # Get site settings
    settings = SiteSettings.get_settings()
    
    context = {
        'featured_products': featured_products,
        'latest_posts': latest_posts,
        'categories': categories,
        'recommendations': recommendations,
        'settings': settings,
    }
    
    return render(request, 'core/welsh_heritage_home.html', context)

def about(request):
    """About page view"""
    settings = SiteSettings.get_settings()
    
    context = {
        'settings': settings,
    }
    
    return render(request, 'core/about.html', context)

def contact(request):
    """Contact page view"""
    settings = SiteSettings.get_settings()
    faqs = FAQ.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if all([name, email, subject, message]):
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            messages.success(request, 'Thank you for your message. We\'ll get back to you soon!')
            return redirect('core:contact')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    context = {
        'settings': settings,
        'faqs': faqs,
    }
    
    return render(request, 'core/contact.html', context)

def search(request):
    """Search functionality"""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'relevance')
    
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    
    # Search query
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    
    # Category filter
    if category_id:
        try:
            category = Category.objects.get(id=category_id, is_active=True)
            products = products.filter(
                Q(category=category) |
                Q(category__parent=category)
            )
        except Category.DoesNotExist:
            pass
    
    # Price filters
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass
    
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass
    
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'rating':
        products = products.order_by('-average_rating')
    else:  # relevance or default
        if query:
            # Simple relevance scoring - can be improved with full-text search
            products = products.extra(
                select={
                    'relevance': """
                        CASE 
                            WHEN name LIKE %s THEN 3
                            WHEN short_description LIKE %s THEN 2
                            ELSE 1
                        END
                    """
                },
                select_params=[f'%{query}%', f'%{query}%']
            ).order_by('-relevance', '-view_count')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter sidebar
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    ).annotate(product_count=Count('products'))
    
    # Get price range
    price_range = Product.objects.filter(is_active=True).aggregate(
        min_price=models.Min('price'),
        max_price=models.Max('price')
    )
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'categories': categories,
        'price_range': price_range,
        'current_filters': {
            'category_id': category_id,
            'min_price': min_price,
            'max_price': max_price,
            'sort_by': sort_by,
        },
        'total_results': paginator.count,
    }
    
    return render(request, 'core/search.html', context)

@require_POST
def newsletter_signup(request):
    """Handle newsletter signup via AJAX"""
    email = request.POST.get('email', '').strip().lower()
    
    if not email:
        return JsonResponse({'success': False, 'message': 'Email is required.'})
    
    # Check if email already exists
    newsletter, created = Newsletter.objects.get_or_create(
        email=email,
        defaults={'is_subscribed': True}
    )
    
    if created:
        messages.success(request, 'Thank you for subscribing to our newsletter!')
        return JsonResponse({'success': True, 'message': 'Successfully subscribed!'})
    elif not newsletter.is_subscribed:
        newsletter.is_subscribed = True
        newsletter.save()
        messages.success(request, 'Welcome back! You\'ve been resubscribed.')
        return JsonResponse({'success': True, 'message': 'Successfully resubscribed!'})
    else:
        return JsonResponse({'success': False, 'message': 'You are already subscribed.'})

def privacy_policy(request):
    """Privacy policy page"""
    return render(request, 'core/privacy_policy.html')

def terms_of_service(request):
    """Terms of service page"""
    return render(request, 'core/terms_of_service.html')

def shipping_info(request):
    """Shipping information page"""
    settings = SiteSettings.get_settings()
    
    context = {
        'settings': settings,
    }
    
    return render(request, 'core/shipping_info.html', context)

def returns_policy(request):
    """Returns policy page"""
    settings = SiteSettings.get_settings()
    
    context = {
        'settings': settings,
    }
    
    return render(request, 'core/returns_policy.html', context)

# AJAX endpoints
@require_POST
def add_to_cart(request):
    """Add product to cart via AJAX"""
    from core.cart import Cart
    
    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found.'})
    
    # Check stock
    if product.manage_stock and product.stock_quantity < quantity:
        return JsonResponse({'success': False, 'message': 'Not enough stock available.'})
    
    cart = Cart(request)
    cart.add(product, quantity=quantity, variant_id=variant_id)
    
    # Track user behavior
    from users.models import UserActivity
    UserActivity.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key,
        activity_type='add_to_cart',
        object_id=str(product.id),
        metadata={'quantity': quantity, 'variant_id': variant_id},
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return JsonResponse({
        'success': True,
        'message': f'{product.name} added to cart!',
        'cart_count': len(cart),
        'cart_total': str(cart.get_total_price())
    })

@require_POST
def remove_from_cart(request):
    """Remove product from cart via AJAX"""
    from core.cart import Cart
    
    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id')
    
    cart = Cart(request)
    cart.remove(product_id, variant_id)
    
    return JsonResponse({
        'success': True,
        'message': 'Item removed from cart',
        'cart_count': len(cart),
        'cart_total': str(cart.get_total_price())
    })

@require_POST  
def update_cart(request):
    """Update cart quantities via AJAX"""
    from core.cart import Cart
    
    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))
    
    cart = Cart(request)
    
    if quantity > 0:
        cart.add(product_id, quantity=quantity, variant_id=variant_id, override_quantity=True)
    else:
        cart.remove(product_id, variant_id)
    
    return JsonResponse({
        'success': True,
        'cart_count': len(cart),
        'cart_total': str(cart.get_total_price())
    })

def cart_detail(request):
    """Cart detail page"""
    from core.cart import Cart
    
    cart = Cart(request)
    
    # Get recommendations for cart
    recommendation_service = RecommendationService()
    recommendations = recommendation_service.get_cart_recommendations(request)
    
    context = {
        'cart': cart,
        'recommendations': recommendations,
    }
    
    return render(request, 'core/cart.html', context)