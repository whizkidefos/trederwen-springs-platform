# core/context_processors.py
from .cart import Cart
from .models import SiteSettings
from products.models import Category

def cart_context(request):
    """Add cart to template context"""
    try:
        cart = Cart(request)
        return {
            'cart': cart,
            'cart_data': cart.get_cart_data(),
        }
    except Exception:
        # Return empty cart data if there's an issue
        return {
            'cart': None,
            'cart_data': {
                'items': [],
                'total_price': 0,
                'total_items': 0,
                'is_empty': True,
            },
        }

def site_context(request):
    """Add site-wide data to template context"""
    try:
        settings = SiteSettings.get_settings()
        
        # Get main navigation categories
        nav_categories = Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).order_by('order', 'name')[:6]
        
        return {
            'site_settings': settings,
            'nav_categories': nav_categories,
        }
    except Exception:
        # Return default data if models aren't ready
        return {
            'site_settings': {
                'site_name': 'Trederwen Springs',
                'site_description': 'Premium Welsh Spring Water',
            },
            'nav_categories': [],
        }