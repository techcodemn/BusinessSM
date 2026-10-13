from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'sku_badge', 'type_badge', 'category',
        'formatted_price', 'formatted_cost', 'stock_badge', 'status_badge'
    )
    list_filter = ('product_type', 'category', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'category', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description="SKU")
    def sku_badge(self, obj):
        return format_html('<code>{}</code>', obj.sku)

    @admin.display(description="Type")
    def type_badge(self, obj):
        if obj.product_type == 'service':
            return mark_safe('<span class="admin-badge-pill admin-badge-purple">Service</span>')
        return mark_safe('<span class="admin-badge-pill admin-badge-info">Product</span>')

    @admin.display(description="Selling Price")
    def formatted_price(self, obj):
        return format_html('<strong>₹{}</strong>', f"{obj.unit_price:,.2f}")

    @admin.display(description="Cost Price")
    def formatted_cost(self, obj):
        return f"₹{obj.cost_price:,.2f}"

    @admin.display(description="Stock Level")
    def stock_badge(self, obj):
        if obj.is_service:
            return mark_safe('<span style="color:#64748b;">— Service</span>')
        if obj.stock_quantity <= 0:
            return mark_safe('<span class="admin-badge-pill admin-badge-danger">Out of Stock (0)</span>')
        if obj.stock_quantity <= 5:
            return format_html('<span class="admin-badge-pill admin-badge-warning">Low Stock ({})</span>', obj.stock_quantity)
        return format_html('<span class="admin-badge-pill admin-badge-success">In Stock ({})</span>', obj.stock_quantity)

    @admin.display(description="Status")
    def status_badge(self, obj):
        if obj.is_active:
            return mark_safe('<span class="admin-badge-pill admin-badge-success">Active</span>')
        return mark_safe('<span class="admin-badge-pill admin-badge-neutral">Inactive</span>')

