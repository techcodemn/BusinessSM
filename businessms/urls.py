"""
URL configuration for businessms project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('customers/', include('customers.urls')),
    path('products/', include('products.urls')),
    path('sales/', include('sales.urls')),
]

# Custom Admin Site Branding
admin.site.site_header = "BusinessMS Administration"
admin.site.site_title = "BusinessMS Admin"
admin.site.index_title = "Database Control & Operations Center"

