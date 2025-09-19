# core/cart.py
from decimal import Decimal
from django.conf import settings
from products.models import Product, ProductVariant

class Cart:
    """Shopping cart functionality"""
    
    def __init__(self, request):
        """Initialize the cart"""
        self.session = request.session
        self.request = request
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
    
    def add(self, product, quantity=1, variant_id=None, override_quantity=False):
        """Add a product to the cart or update its quantity"""
        if isinstance(product, str):
            product_id = product
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return
        else:
            product_id = str(product.id)
        
        # Create unique key for product + variant combination
        cart_key = f"{product_id}"
        if variant_id:
            cart_key += f"_v{variant_id}"
        
        # Get variant if specified
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
            except ProductVariant.DoesNotExist:
                pass
        
        # Get price (use variant price if available)
        price = variant.effective_price if variant else product.price
        
        if cart_key not in self.cart:
            self.cart[cart_key] = {
                'product_id': product_id,
                'variant_id': variant_id,
                'quantity': 0,
                'price': str(price),
                'name': product.name,
                'image_url': product.images.first().image.url if product.images.exists() else None,
            }
        
        if override_quantity:
            self.cart[cart_key]['quantity'] = quantity
        else:
            self.cart[cart_key]['quantity'] += quantity
        
        # Update price in case it changed
        self.cart[cart_key]['price'] = str(price)
        
        self.save()
    
    def save(self):
        """Mark the session as modified to ensure it gets saved"""
        self.session.modified = True
    
    def remove(self, product_id, variant_id=None):
        """Remove a product from the cart"""
        cart_key = f"{product_id}"
        if variant_id:
            cart_key += f"_v{variant_id}"
        
        if cart_key in self.cart:
            del self.cart[cart_key]
            self.save()
    
    def clear(self):
        """Clear the cart"""
        del self.session[settings.CART_SESSION_ID]
        self.save()
    
    def get_total_price(self):
        """Calculate total price of all items in cart"""
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
    
    def get_total_items(self):
        """Get total number of items in cart"""
        return sum(item['quantity'] for item in self.cart.values())
    
    def __len__(self):
        """Count all items in the cart"""
        return sum(item['quantity'] for item in self.cart.values())
    
    def __iter__(self):
        """Iterate over the items in the cart and get the products from the database"""
        product_ids = []
        variant_ids = []
        
        for item in self.cart.values():
            product_ids.append(item['product_id'])
            if item.get('variant_id'):
                variant_ids.append(item['variant_id'])
        
        # Get products from database
        products = Product.objects.filter(id__in=product_ids)
        variants = {}
        if variant_ids:
            for variant in ProductVariant.objects.filter(id__in=variant_ids):
                variants[str(variant.id)] = variant
        
        cart = self.cart.copy()
        for item in cart.values():
            product_id = item['product_id']
            variant_id = item.get('variant_id')
            
            # Find the product
            product = None
            for p in products:
                if str(p.id) == product_id:
                    product = p
                    break
            
            if product:
                item['product'] = product
                item['variant'] = variants.get(variant_id) if variant_id else None
                item['total_price'] = Decimal(item['price']) * item['quantity']
                item['update_quantity_url'] = f"/ajax/update-cart/"
                item['remove_url'] = f"/ajax/remove-from-cart/"
                yield item
    
    def get_cart_data(self):
        """Get cart data for templates"""
        items = list(self)
        return {
            'items': items,
            'total_price': self.get_total_price(),
            'total_items': self.get_total_items(),
            'is_empty': len(self.cart) == 0,
        }
    
    def get_product_quantity(self, product_id, variant_id=None):
        """Get quantity of a specific product in cart"""
        cart_key = f"{product_id}"
        if variant_id:
            cart_key += f"_v{variant_id}"
        
        if cart_key in self.cart:
            return self.cart[cart_key]['quantity']
        return 0