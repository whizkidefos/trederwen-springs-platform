"""
URL configuration for trederwen_springs project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('accounts/', include('users.urls')),
    path('blog/', include('blog.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('api/recommendations/', include('ai_recommendations.urls')),
    path('dashboard/', include('dashboard.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Admin site customization
admin.site.site_header = 'Trederwen Springs Admin'
admin.site.site_title = 'Trederwen Springs Admin Portal'
admin.site.index_title = 'Welcome to Trederwen Springs Administration'