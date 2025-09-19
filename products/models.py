# products/models.py
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from core.models import BaseModel
import os

User = get_user_model()

class Category(BaseModel):
    """Product categories"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    seo_title = models.CharField(max_length=60, blank=True)
    seo_description = models.TextField(max_length=160, blank=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:category', kwargs={'slug': self.slug})

class Brand(BaseModel):
    """Product brands"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(BaseModel):
    """Main product model"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    short_description = models.TextField(max_length=500, blank=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.CASCADE, null=True, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Inventory
    sku = models.CharField(max_length=100, unique=True)
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    manage_stock = models.BooleanField(default=True)
    
    # Physical properties
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Weight in grams")
    dimensions = models.JSONField(default=dict, blank=True, help_text="Length, width, height in cm")
    
    # Product attributes
    ingredients = models.TextField(blank=True)
    nutritional_info = models.JSONField(default=dict, blank=True)
    allergens = models.JSONField(default=list, blank=True)
    features = models.JSONField(default=list, blank=True)
    
    # Status and visibility
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_digital = models.BooleanField(default=False)
    requires_shipping = models.BooleanField(default=True)
    
    # SEO
    seo_title = models.CharField(max_length=60, blank=True)
    seo_description = models.TextField(max_length=160, blank=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.short_description:
            self.short_description = self.description[:500]
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})
    
    @property
    def is_in_stock(self):
        if not self.manage_stock:
            return True
        return self.stock_quantity > 0
    
    @property
    def in_stock(self):
        """Alias for is_in_stock for template compatibility"""
        return self.is_in_stock
    
    @property
    def is_low_stock(self):
        if not self.manage_stock:
            return False
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def discount_percentage(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return round(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0
    
    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0
    
    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()
    
    def increment_view_count(self):
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])

class ProductImage(BaseModel):
    """Product images"""
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.order}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary image per product
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        if not self.alt_text:
            self.alt_text = f"{self.product.name} image"
        super().save(*args, **kwargs)

class ProductVariant(BaseModel):
    """Product variants (size, flavor, etc.)"""
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(default=0)
    attributes = models.JSONField(default=dict)  # e.g., {"size": "500ml", "flavor": "Lemon"}
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    @property
    def effective_price(self):
        return self.price or self.product.price
    
    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

class ProductReview(BaseModel):
    """Product reviews"""
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    review = models.TextField()
    is_approved = models.BooleanField(default=False)
    is_verified_purchase = models.BooleanField(default=False)
    helpful_votes = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.rating} stars by {self.user.get_full_name()}"

class ProductAttribute(BaseModel):
    """Product attributes (e.g., color, size, flavor)"""
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, blank=True)
    is_variation = models.BooleanField(default=True, help_text="Can be used for product variations")
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class ProductAttributeValue(BaseModel):
    """Values for product attributes"""
    attribute = models.ForeignKey(ProductAttribute, related_name='values', on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)
    color_code = models.CharField(max_length=7, blank=True, help_text="Hex color code for color attributes")
    
    class Meta:
        unique_together = ('attribute', 'value')
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.value)
        super().save(*args, **kwargs)

class ProductAttributeAssignment(models.Model):
    """Assign attributes to products"""
    product = models.ForeignKey(Product, related_name='attribute_assignments', on_delete=models.CASCADE)
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    values = models.ManyToManyField(ProductAttributeValue)
    
    class Meta:
        unique_together = ('product', 'attribute')
    
    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}"

class Wishlist(BaseModel):
    """User wishlists"""
    user = models.ForeignKey(User, related_name='wishlists', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="My Wishlist")
    is_default = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.name}"

class WishlistItem(models.Model):
    """Items in wishlists"""
    wishlist = models.ForeignKey(Wishlist, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('wishlist', 'product', 'variant')
    
    def __str__(self):
        return f"{self.wishlist.name} - {self.product.name}"

class ProductTag(BaseModel):
    """Tags for products"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    color = models.CharField(max_length=7, default="#007bff")
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

# Add tags to products through a many-to-many relationship
Product.add_to_class('tags', models.ManyToManyField(ProductTag, blank=True, related_name='products'))