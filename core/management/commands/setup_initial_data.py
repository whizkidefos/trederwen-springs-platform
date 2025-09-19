# core/management/commands/setup_initial_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from core.models import SiteSettings, FAQ
from products.models import Category, Brand, Product, ProductImage, ProductTag
from blog.models import BlogCategory, BlogPost
from orders.models import ShippingMethod, Coupon
from subscriptions.models import SubscriptionPlan
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup initial data for Trederwen Springs website'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--with-sample-data',
            action='store_true',
            help='Create sample products and content',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create site settings
        self.create_site_settings()
        
        # Create shipping methods
        self.create_shipping_methods()
        
        # Create subscription plans
        self.create_subscription_plans()
        
        # Create FAQs
        self.create_faqs()
        
        # Create admin user if it doesn't exist
        self.create_admin_user()
        
        if options['with_sample_data']:
            self.stdout.write('Creating sample data...')
            self.create_sample_categories()
            self.create_sample_brands()
            self.create_sample_products()
            self.create_sample_blog_content()
            self.create_sample_coupons()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up initial data!')
        )
    
    def create_site_settings(self):
        """Create default site settings"""
        settings, created = SiteSettings.objects.get_or_create(
            defaults={
                'site_name': 'Trederwen Springs',
                'site_description': 'Premium Welsh Spring Water - Pure, Natural, Refreshing',
                'contact_email': 'info@trederwensprings.co.uk',
                'contact_phone': '+44 1234 567890',
                'address': 'Welsh Mountains, Wales, UK',
                'delivery_info': 'Free delivery on orders over £25. Next-day delivery available.',
                'returns_policy': '30-day money-back guarantee on all products.',
            }
        )
        
        if created:
            self.stdout.write('✓ Created site settings')
        else:
            self.stdout.write('• Site settings already exist')
    
    def create_shipping_methods(self):
        """Create shipping methods"""
        shipping_methods = [
            {
                'name': 'Standard Delivery',
                'description': 'Free standard delivery on orders over £25',
                'price': Decimal('4.99'),
                'estimated_days_min': 3,
                'estimated_days_max': 5,
                'free_shipping_threshold': Decimal('25.00'),
            },
            {
                'name': 'Express Delivery',
                'description': 'Next working day delivery',
                'price': Decimal('9.99'),
                'estimated_days_min': 1,
                'estimated_days_max': 1,
            },
            {
                'name': 'Premium Delivery',
                'description': 'Same day delivery (selected areas)',
                'price': Decimal('14.99'),
                'estimated_days_min': 0,
                'estimated_days_max': 0,
            },
        ]
        
        created_count = 0
        for method_data in shipping_methods:
            method, created = ShippingMethod.objects.get_or_create(
                name=method_data['name'],
                defaults=method_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} shipping methods')
    
    def create_subscription_plans(self):
        """Create subscription plans"""
        plans = [
            {
                'name': 'Weekly Refresh',
                'description': 'Perfect for regular water consumption. Get fresh Welsh spring water delivered every week.',
                'billing_interval': 'weekly',
                'interval_count': 1,
                'base_price': Decimal('12.99'),
                'discount_percentage': Decimal('10.00'),
                'free_shipping': True,
                'flexible_delivery': True,
            },
            {
                'name': 'Monthly Essentials',
                'description': 'Ideal for families. Monthly delivery of premium spring water with significant savings.',
                'billing_interval': 'monthly',
                'interval_count': 1,
                'base_price': Decimal('45.99'),
                'discount_percentage': Decimal('15.00'),
                'free_shipping': True,
                'priority_support': True,
                'flexible_delivery': True,
            },
            {
                'name': 'Quarterly Premium',
                'description': 'Best value option. Quarterly deliveries with maximum savings and exclusive benefits.',
                'billing_interval': 'quarterly',
                'interval_count': 1,
                'base_price': Decimal('120.99'),
                'discount_percentage': Decimal('20.00'),
                'free_shipping': True,
                'priority_support': True,
                'exclusive_products': True,
                'flexible_delivery': True,
            },
        ]
        
        created_count = 0
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} subscription plans')
    
    def create_faqs(self):
        """Create FAQ entries"""
        faqs = [
            {
                'question': 'What makes Trederwen Springs water special?',
                'answer': 'Our water is naturally filtered through ancient Welsh rock formations over many years, giving it a unique mineral composition and pure taste that\'s perfect for drinking and brewing.',
                'order': 1,
            },
            {
                'question': 'Do you offer subscription services?',
                'answer': 'Yes! We offer flexible subscription plans with weekly, monthly, and quarterly deliveries. Subscribers enjoy discounts, free shipping, and the convenience of regular deliveries.',
                'order': 2,
            },
            {
                'question': 'What are your delivery options?',
                'answer': 'We offer standard delivery (3-5 days), express next-day delivery, and same-day delivery in selected areas. Free standard delivery is available on orders over £25.',
                'order': 3,
            },
            {
                'question': 'Is your packaging environmentally friendly?',
                'answer': 'Absolutely! We use recyclable materials and are committed to sustainable packaging solutions. Our bottles are made from recycled materials and are fully recyclable.',
                'order': 4,
            },
            {
                'question': 'Can I cancel my subscription anytime?',
                'answer': 'Yes, you can pause, modify, or cancel your subscription at any time through your account dashboard or by contacting our customer service team.',
                'order': 5,
            },
        ]
        
        created_count = 0
        for faq_data in faqs:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} FAQ entries')
    
    def create_admin_user(self):
        """Create admin user if it doesn't exist"""
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@trederwensprings.co.uk',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write('✓ Created admin user (admin/admin123)')
        else:
            self.stdout.write('• Admin user already exists')
    
    def create_sample_categories(self):
        """Create sample product categories"""
        categories = [
            {
                'name': 'Spring Water',
                'description': 'Pure Welsh spring water in various sizes',
                'order': 1,
            },
            {
                'name': 'Sparkling Water',
                'description': 'Naturally carbonated spring water',
                'order': 2,
            },
            {
                'name': 'Flavoured Water',
                'description': 'Spring water with natural fruit flavours',
                'order': 3,
            },
            {
                'name': 'Coffee & Tea',
                'description': 'Premium blends for brewing with our spring water',
                'order': 4,
            },
            {
                'name': 'Wellness',
                'description': 'Enhanced waters for health and wellness',
                'order': 5,
            },
            {
                'name': 'Gift Sets',
                'description': 'Curated collections perfect for gifting',
                'order': 6,
            },
        ]
        
        created_count = 0
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} categories')
    
    def create_sample_brands(self):
        """Create sample brands"""
        brands = [
            {
                'name': 'Trederwen Springs',
                'description': 'Our flagship brand of premium Welsh spring water',
            },
            {
                'name': 'Mountain Pure',
                'description': 'Artisanal spring water from the highest peaks',
            },
            {
                'name': 'Welsh Heritage',
                'description': 'Traditional spring water with centuries of history',
            },
        ]
        
        created_count = 0
        for brand_data in brands:
            brand, created = Brand.objects.get_or_create(
                name=brand_data['name'],
                defaults=brand_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} brands')
    
    def create_sample_products(self):
        """Create sample products"""
        if not Category.objects.exists() or not Brand.objects.exists():
            self.stdout.write('• Skipping products - no categories or brands')
            return
        
        spring_water = Category.objects.get(name='Spring Water')
        sparkling = Category.objects.get(name='Sparkling Water')
        flavoured = Category.objects.get(name='Flavoured Water')
        
        trederwen_brand = Brand.objects.get(name='Trederwen Springs')
        mountain_brand = Brand.objects.get(name='Mountain Pure')
        
        products = [
            {
                'name': 'Pure Welsh Spring Water 500ml',
                'description': 'Our signature 500ml bottle of pure Welsh spring water. Perfect for on-the-go hydration with the crisp, clean taste of Wales.',
                'short_description': 'Pure Welsh spring water in convenient 500ml bottles.',
                'category': spring_water,
                'brand': trederwen_brand,
                'price': Decimal('1.99'),
                'compare_at_price': Decimal('2.49'),
                'sku': 'TSW-500ML-001',
                'stock_quantity': 100,
                'weight': Decimal('500'),
                'is_featured': True,
                'ingredients': 'Pure Welsh spring water',
                'features': ['BPA-free bottle', 'Recyclable packaging', 'Natural minerals'],
            },
            {
                'name': 'Pure Welsh Spring Water 1.5L',
                'description': 'Family-size 1.5L bottle perfect for sharing. Our premium spring water sourced from the pristine Welsh mountains.',
                'short_description': 'Family-size 1.5L bottle of pure Welsh spring water.',
                'category': spring_water,
                'brand': trederwen_brand,
                'price': Decimal('3.99'),
                'compare_at_price': Decimal('4.99'),
                'sku': 'TSW-1500ML-001',
                'stock_quantity': 75,
                'weight': Decimal('1500'),
                'is_featured': True,
                'ingredients': 'Pure Welsh spring water',
                'features': ['Family size', 'BPA-free bottle', 'Recyclable packaging'],
            },
            {
                'name': 'Sparkling Welsh Spring Water 500ml',
                'description': 'Naturally carbonated Welsh spring water with a refreshing sparkle. Perfect for special occasions or when you want something extra.',
                'short_description': 'Naturally sparkling Welsh spring water.',
                'category': sparkling,
                'brand': trederwen_brand,
                'price': Decimal('2.49'),
                'sku': 'TSS-500ML-001',
                'stock_quantity': 80,
                'weight': Decimal('500'),
                'ingredients': 'Welsh spring water, natural carbonation',
                'features': ['Naturally carbonated', 'Zero calories', 'Premium glass bottle'],
            },
            {
                'name': 'Lemon & Lime Flavoured Water 500ml',
                'description': 'Refreshing spring water infused with natural lemon and lime flavours. A guilt-free way to stay hydrated with a burst of citrus.',
                'short_description': 'Spring water with natural lemon and lime flavours.',
                'category': flavoured,
                'brand': trederwen_brand,
                'price': Decimal('2.99'),
                'sku': 'TFL-LEMON-500',
                'stock_quantity': 60,
                'weight': Decimal('500'),
                'ingredients': 'Welsh spring water, natural lemon flavour, natural lime flavour',
                'features': ['No artificial sweeteners', 'Natural flavours only', 'Zero calories'],
            },
            {
                'name': 'Mountain Pure Spring Water 750ml',
                'description': 'Premium artisanal spring water from the highest Welsh peaks. Presented in an elegant glass bottle, perfect for fine dining.',
                'short_description': 'Premium artisanal spring water in elegant glass bottle.',
                'category': spring_water,
                'brand': mountain_brand,
                'price': Decimal('4.99'),
                'sku': 'MP-750ML-001',
                'stock_quantity': 40,
                'weight': Decimal('750'),
                'is_featured': True,
                'ingredients': 'Artisanal Welsh spring water',
                'features': ['Premium glass bottle', 'Limited edition', 'Perfect for fine dining'],
            },
            {
                'name': 'Berry Burst Flavoured Water 500ml',
                'description': 'Delicious spring water infused with natural berry flavours. A healthy alternative to sugary drinks with the taste of summer berries.',
                'short_description': 'Spring water with natural mixed berry flavours.',
                'category': flavoured,
                'brand': trederwen_brand,
                'price': Decimal('2.99'),
                'sku': 'TFL-BERRY-500',
                'stock_quantity': 55,
                'weight': Decimal('500'),
                'ingredients': 'Welsh spring water, natural berry flavours',
                'features': ['Mixed berry taste', 'No added sugar', 'Antioxidant-rich'],
            },
        ]
        
        # Create product tags
        tags = ['Premium', 'Natural', 'Refreshing', 'Healthy', 'Welsh', 'Eco-Friendly']
        for tag_name in tags:
            ProductTag.objects.get_or_create(name=tag_name)
        
        created_count = 0
        for product_data in products:
            product, created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults=product_data
            )
            
            if created:
                # Add random tags
                available_tags = list(ProductTag.objects.all())
                product.tags.set(random.sample(available_tags, random.randint(2, 4)))
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} products')
    
    def create_sample_blog_content(self):
        """Create sample blog posts"""
        # Create blog categories
        blog_categories = [
            {'name': 'Health & Wellness', 'color': '#10B981'},
            {'name': 'Sustainability', 'color': '#059669'},
            {'name': 'Recipes', 'color': '#DC2626'},
            {'name': 'Company News', 'color': '#2563EB'},
        ]
        
        for cat_data in blog_categories:
            BlogCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
        
        # Create admin user for blog posts
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            return
        
        wellness_cat = BlogCategory.objects.get(name='Health & Wellness')
        sustainability_cat = BlogCategory.objects.get(name='Sustainability')
        
        blog_posts = [
            {
                'title': 'The Health Benefits of Staying Hydrated',
                'excerpt': 'Discover why proper hydration is essential for your health and how Welsh spring water can be part of your wellness journey.',
                'content': '''
                <p>Proper hydration is one of the most important aspects of maintaining good health. Our bodies are approximately 60% water, and every system depends on water to function properly.</p>
                
                <h2>Why Hydration Matters</h2>
                <p>Water plays crucial roles in our body including:</p>
                <ul>
                    <li>Regulating body temperature</li>
                    <li>Lubricating joints</li>
                    <li>Transporting nutrients</li>
                    <li>Removing waste products</li>
                </ul>
                
                <h2>Quality Matters</h2>
                <p>Not all water is created equal. Pure Welsh spring water provides essential minerals while maintaining the clean, refreshing taste that encourages regular consumption.</p>
                ''',
                'author': admin_user,
                'category': wellness_cat,
                'status': 'published',
                'published_at': timezone.now() - timedelta(days=2),
                'is_featured': True,
            },
            {
                'title': 'Our Commitment to Sustainable Packaging',
                'excerpt': 'Learn about our environmental initiatives and how we\'re working to reduce our carbon footprint while delivering premium water.',
                'content': '''
                <p>At Trederwen Springs, we believe that protecting the environment that gives us our pure spring water is not just a responsibility—it's a passion.</p>
                
                <h2>Recyclable Materials</h2>
                <p>All our bottles are made from 100% recyclable materials. We've also reduced plastic usage by 30% over the past two years.</p>
                
                <h2>Carbon Neutral Delivery</h2>
                <p>We're proud to offer carbon-neutral delivery options and are working toward making all our deliveries carbon neutral by 2025.</p>
                ''',
                'author': admin_user,
                'category': sustainability_cat,
                'status': 'published',
                'published_at': timezone.now() - timedelta(days=5),
                'is_featured': True,
            },
        ]
        
        created_count = 0
        for post_data in blog_posts:
            post, created = BlogPost.objects.get_or_create(
                title=post_data['title'],
                defaults=post_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} blog posts')
    
    def create_sample_coupons(self):
        """Create sample discount coupons"""
        now = timezone.now()
        
        coupons = [
            {
                'code': 'WELCOME10',
                'description': 'Welcome offer - 10% off your first order',
                'discount_type': 'percentage',
                'discount_value': Decimal('10.00'),
                'minimum_order_amount': Decimal('20.00'),
                'usage_limit': 1000,
                'user_usage_limit': 1,
                'valid_from': now,
                'valid_until': now + timedelta(days=90),
            },
            {
                'code': 'FREESHIP',
                'description': 'Free shipping on any order',
                'discount_type': 'free_shipping',
                'discount_value': Decimal('0.00'),
                'valid_from': now,
                'valid_until': now + timedelta(days=30),
            },
            {
                'code': 'SUMMER25',
                'description': 'Summer special - £25 off orders over £100',
                'discount_type': 'fixed_amount',
                'discount_value': Decimal('25.00'),
                'minimum_order_amount': Decimal('100.00'),
                'usage_limit': 500,
                'valid_from': now,
                'valid_until': now + timedelta(days=60),
            },
        ]
        
        created_count = 0
        for coupon_data in coupons:
            coupon, created = Coupon.objects.get_or_create(
                code=coupon_data['code'],
                defaults=coupon_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} coupons')