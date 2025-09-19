from django.contrib import admin
from .models import (BlogCategory, BlogTag, BlogPost, BlogComment, 
                    BlogSubscriber, Recipe, BlogSeries)

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order', 'published_posts_count']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']

@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'published_at', 'view_count']
    list_filter = ['status', 'category', 'is_featured', 'published_at', 'created_at']
    search_fields = ['title', 'content', 'author__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'reading_time']
    filter_horizontal = ['tags', 'related_products']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'author', 'category')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt')
        }),
        ('Publishing', {
            'fields': ('status', 'published_at', 'scheduled_at')
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description')
        }),
        ('Options', {
            'fields': ('is_featured', 'allow_comments', 'series', 'series_order')
        }),
        ('Related Content', {
            'fields': ('tags', 'related_products')
        }),
        ('Analytics', {
            'fields': ('view_count', 'reading_time', 'like_count'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_posts', 'unpublish_posts', 'feature_posts']
    
    def publish_posts(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} posts were published.')
    
    def unpublish_posts(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} posts were unpublished.')
    
    def feature_posts(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} posts were featured.')

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author_name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['post__title', 'author_name', 'author_email', 'content']
    actions = ['approve_comments', 'reject_comments']
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} comments were approved.')
    
    def reject_comments(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} comments were rejected.')

@admin.register(BlogSubscriber)
class BlogSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_confirmed', 'is_active', 'frequency']
    list_filter = ['is_confirmed', 'is_active', 'frequency']
    search_fields = ['email', 'name']

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'difficulty', 'prep_time', 'total_time', 'is_published']
    list_filter = ['difficulty', 'is_published', 'author']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['related_products']

@admin.register(BlogSeries)
class BlogSeriesAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'post_count']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}