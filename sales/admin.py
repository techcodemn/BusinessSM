from django.contrib import admin
from django.utils.html import format_html
from .models import Invoice, InvoiceItem, Payment


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('product', 'description', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ('payment_date', 'amount', 'payment_method', 'reference_number', 'notes', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'customer_link', 'status_badge',
        'formatted_total', 'formatted_paid', 'formatted_balance',
        'issue_date', 'due_date'
    )
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'customer__name', 'customer__company', 'customer__email')
    readonly_fields = ('subtotal', 'tax_amount', 'total_amount', 'paid_amount', 'balance_due', 'created_at', 'updated_at')
    date_hierarchy = 'issue_date'
    inlines = [InvoiceItemInline, PaymentInline]

    @admin.display(description="Customer")
    def customer_link(self, obj):
        return f"{obj.customer.name} ({obj.customer.company})" if obj.customer.company else obj.customer.name

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            'paid': 'admin-badge-success',
            'partial': 'admin-badge-warning',
            'unpaid': 'admin-badge-danger',
            'overdue': 'admin-badge-danger',
            'sent': 'admin-badge-info',
            'draft': 'admin-badge-neutral',
            'cancelled': 'admin-badge-neutral',
        }
        badge_cls = colors.get(obj.status, 'admin-badge-neutral')
        return format_html('<span class="admin-badge-pill {}">{}</span>', badge_cls, obj.get_status_display())

    @admin.display(description="Total")
    def formatted_total(self, obj):
        return f"₹{obj.total_amount:,.2f}"

    @admin.display(description="Paid")
    def formatted_paid(self, obj):
        return format_html('<span style="color:#059669; font-weight:600;">₹{}</span>', f"{obj.paid_amount:,.2f}")

    @admin.display(description="Balance")
    def formatted_balance(self, obj):
        color = "#dc2626" if obj.balance_due > 0 else "#059669"
        return format_html('<span style="color:{}; font-weight:600;">₹{}</span>', color, f"{obj.balance_due:,.2f}")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice_link', 'formatted_amount', 'method_badge', 'reference_number', 'payment_date', 'created_at')
    list_filter = ('payment_method', 'payment_date', 'created_at')
    search_fields = ('invoice__invoice_number', 'invoice__customer__name', 'reference_number')
    readonly_fields = ('created_at',)
    date_hierarchy = 'payment_date'

    @admin.display(description="Invoice #")
    def invoice_link(self, obj):
        return f"{obj.invoice.invoice_number} - {obj.invoice.customer.name}"

    @admin.display(description="Amount")
    def formatted_amount(self, obj):
        return format_html('<span style="color:#059669; font-weight:700;">+₹{}</span>', f"{obj.amount:,.2f}")

    @admin.display(description="Method")
    def method_badge(self, obj):
        return format_html('<span class="admin-badge-pill admin-badge-info">{}</span>', obj.get_payment_method_display())

