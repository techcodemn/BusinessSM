from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'company', 'email_link', 'phone', 'city',
        'invoices_count', 'formatted_spent', 'status_badge', 'created_at'
    )
    list_filter = ('is_active', 'city', 'created_at')
    search_fields = ('name', 'company', 'email', 'phone', 'city')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description="Email")
    def email_link(self, obj):
        return format_html('<a href="mailto:{}">{}</a>', obj.email, obj.email)

    @admin.display(description="Invoices")
    def invoices_count(self, obj):
        count = obj.invoices.count()
        return format_html('<span class="admin-badge-pill admin-badge-info">{} Inv</span>', count)

    @admin.display(description="Total Spent")
    def formatted_spent(self, obj):
        return format_html('<strong style="color:#059669;">₹{}</strong>', f"{obj.total_spent:,.2f}")

    @admin.display(description="Status")
    def status_badge(self, obj):
        if obj.is_active:
            return mark_safe('<span class="admin-badge-pill admin-badge-success">Active</span>')
        return mark_safe('<span class="admin-badge-pill admin-badge-neutral">Inactive</span>')

