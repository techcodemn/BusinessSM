from django import template
from django.db.models import Sum
from customers.models import Customer
from products.models import Product
from sales.models import Invoice, Payment
from django.contrib.auth import get_user_model

register = template.Library()
User = get_user_model()


@register.simple_tag
def get_business_admin_stats():
    """Returns database summary statistics for admin dashboard."""
    customers_count = Customer.objects.count()
    products_count = Product.objects.count()
    invoices_count = Invoice.objects.count()
    payments_count = Payment.objects.count()
    users_count = User.objects.count()

    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = Invoice.objects.filter(status__in=['unpaid', 'partial', 'sent', 'overdue']).aggregate(total=Sum('balance_due'))['total'] or 0

    return {
        'customers_count': customers_count,
        'products_count': products_count,
        'invoices_count': invoices_count,
        'payments_count': payments_count,
        'users_count': users_count,
        'total_revenue': float(total_revenue),
        'pending_amount': float(pending_amount),
    }
