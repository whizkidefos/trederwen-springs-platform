# blog/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from core.models import BaseModel

User = get_user_model()

class BlogCategory(BaseModel):
    """Blog post categories"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#007bff", help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Blog Categories"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:category', kwargs={'slug': self.slug})
    
    @property
    def published_posts_count(self):
        return self.posts.filter(status='published').count()

class BlogTag(BaseModel):
    """Blog post tags"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:tag', kwargs={'slug': self.slug})

class BlogPost(BaseModel):
    """Blog post model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    excerpt = models.TextField(max_length=500, help_text="Brief description of the post")
    content = models.TextField()
    
    # Metadata
    author = models.ForeignKey(User, related_name='blog_posts', on_delete=models.CASCADE)
    category = models.ForeignKey(BlogCategory, related_name='posts', on_delete=models.CASCADE)
    tags = models.ManyToManyField(BlogTag, related_name='posts', blank=True)
    
    # Images
    featured_image = models.ImageField(upload_to='blog/featured/', blank=True, null=True)
    featured_image_alt = models.CharField(max_length=200, blank=True)
    
    # Publishing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    
    # SEO
    seo_title = models.CharField(max_length=60, blank=True)
    seo_description = models.TextField(max_length=160, blank=True)
    
    # Engagement
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    
    # Features
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    
    # Related products
    related_products = models.ManyToManyField('products.Product', related_name='blog_posts', blank=True)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        # Auto-set SEO fields if not provided
        if not self.seo_title:
            self.seo_title = self.title[:60]
        if not self.seo_description:
            self.seo_description = self.excerpt[:160]
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self):
        return self.status == 'published' and self.published_at and self.published_at <= timezone.now()
    
    @property
    def reading_time(self):
        """Estimate reading time in minutes"""
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))  # Assume 200 words per minute
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])

class BlogComment(BaseModel):
    """Blog post comments"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('spam', 'Spam'),
    ]
    
    post = models.ForeignKey(BlogPost, related_name='comments', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', related_name='replies', on_delete=models.CASCADE, null=True, blank=True)
    
    # Author info
    author = models.ForeignKey(User, related_name='blog_comments', on_delete=models.CASCADE, null=True, blank=True)
    author_name = models.CharField(max_length=100, blank=True)
    author_email = models.EmailField(blank=True)
    author_website = models.URLField(blank=True)
    
    # Content
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        author = self.author.get_full_name() if self.author else self.author_name
        return f"Comment by {author} on {self.post.title}"
    
    def save(self, *args, **kwargs):
        # Auto-fill author info if user is logged in
        if self.author and not self.author_name:
            self.author_name = self.author.get_full_name()
        if self.author and not self.author_email:
            self.author_email = self.author.email
        super().save(*args, **kwargs)
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    def approve(self):
        """Approve the comment"""
        self.status = 'approved'
        self.save()
    
    def reject(self):
        """Reject the comment"""
        self.status = 'rejected'
        self.save()

class BlogSubscriber(BaseModel):
    """Blog newsletter subscribers"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_confirmed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    confirmation_token = models.CharField(max_length=100, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Preferences
    categories = models.ManyToManyField(BlogCategory, blank=True, help_text="Categories to receive updates for")
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest'),
        ],
        default='weekly'
    )
    
    def __str__(self):
        return self.email
    
    def confirm_subscription(self):
        """Confirm email subscription"""
        self.is_confirmed = True
        self.confirmed_at = timezone.now()
        self.save()

class Recipe(BaseModel):
    """Recipe model for blog integration"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    
    # Recipe details
    prep_time = models.PositiveIntegerField(help_text="Preparation time in minutes")
    cook_time = models.PositiveIntegerField(help_text="Cooking time in minutes", null=True, blank=True)
    total_time = models.PositiveIntegerField(help_text="Total time in minutes", null=True, blank=True)
    servings = models.PositiveIntegerField(default=1)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    
    # Content
    ingredients = models.JSONField(default=list, help_text="List of ingredients")
    instructions = models.JSONField(default=list, help_text="List of cooking instructions")
    notes = models.TextField(blank=True)
    
    # Images
    featured_image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    
    # Metadata
    author = models.ForeignKey(User, related_name='recipes', on_delete=models.CASCADE)
    category = models.ForeignKey(BlogCategory, related_name='recipes', on_delete=models.CASCADE, null=True, blank=True)
    
    # Nutrition (optional)
    nutrition_info = models.JSONField(default=dict, blank=True, help_text="Calories, protein, etc.")
    
    # Related
    blog_post = models.OneToOneField(BlogPost, on_delete=models.CASCADE, null=True, blank=True, related_name='recipe')
    related_products = models.ManyToManyField('products.Product', blank=True, help_text="Products used in this recipe")
    
    # Status
    is_published = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Calculate total time if not provided
        if not self.total_time and self.prep_time:
            self.total_time = self.prep_time + (self.cook_time or 0)
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:recipe_detail', kwargs={'slug': self.slug})

class BlogImage(BaseModel):
    """Images for blog posts"""
    post = models.ForeignKey(BlogPost, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='blog/images/')
    caption = models.CharField(max_length=300, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.post.title}"
    
    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = f"Image for {self.post.title}"
        super().save(*args, **kwargs)

class BlogSeries(BaseModel):
    """Blog post series"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='blog/series/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:series', kwargs={'slug': self.slug})
    
    @property
    def post_count(self):
        return self.posts.filter(status='published').count()

# Add series field to BlogPost
BlogPost.add_to_class('series', models.ForeignKey(BlogSeries, related_name='posts', on_delete=models.SET_NULL, null=True, blank=True))
BlogPost.add_to_class('series_order', models.PositiveIntegerField(null=True, blank=True))

class BlogAnalytics(BaseModel):
    """Blog analytics data"""
    post = models.OneToOneField(BlogPost, on_delete=models.CASCADE, related_name='analytics')
    
    # Traffic metrics
    unique_views = models.PositiveIntegerField(default=0)
    page_views = models.PositiveIntegerField(default=0)
    bounce_rate = models.FloatField(default=0.0)
    avg_time_on_page = models.DurationField(null=True, blank=True)
    
    # Engagement metrics
    social_shares = models.PositiveIntegerField(default=0)
    email_shares = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    
    # Traffic sources
    organic_traffic = models.PositiveIntegerField(default=0)
    direct_traffic = models.PositiveIntegerField(default=0)
    social_traffic = models.PositiveIntegerField(default=0)
    referral_traffic = models.PositiveIntegerField(default=0)
    
    # Conversion metrics
    product_clicks = models.PositiveIntegerField(default=0)
    newsletter_signups = models.PositiveIntegerField(default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.post.title}"
    
    def update_comment_count(self):
        """Update comment count from actual comments"""
        self.comment_count = self.post.comments.filter(status='approved').count()
        self.save(update_fields=['comment_count'])

class PopularPost(models.Model):
    """Track popular posts for different time periods"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='popularity_data')
    period = models.CharField(max_length=10, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ])
    rank = models.PositiveIntegerField()
    view_count = models.PositiveIntegerField()
    date = models.DateField()
    
    class Meta:
        unique_together = ('post', 'period', 'date')
        ordering = ['period', 'date', 'rank']
    
    def __str__(self):
        return f"{self.post.title} - #{self.rank} ({self.period})"