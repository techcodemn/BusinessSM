from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
import json

from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from customers.models import Customer
from products.models import Product
from sales.models import Invoice, Payment


@login_required
def dashboard(request):
    # Customer metrics
    total_customers = Customer.objects.count()
    active_customers = Customer.objects.filter(is_active=True).count()

    # Product metrics
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(product_type='product', stock_quantity__lte=5, stock_quantity__gt=0)
    out_of_stock_products = Product.objects.filter(product_type='product', stock_quantity__lte=0)
    low_stock_count = low_stock_products.count() + out_of_stock_products.count()

    # Financial / Invoice metrics
    invoices = Invoice.objects.exclude(status='cancelled')
    total_sales = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_pending = invoices.aggregate(Sum('balance_due'))['balance_due__sum'] or Decimal('0.00')

    # Invoice Status Counts
    invoice_counts = {
        'total': Invoice.objects.count(),
        'paid': Invoice.objects.filter(status='paid').count(),
        'unpaid': Invoice.objects.filter(status='unpaid').count(),
        'partial': Invoice.objects.filter(status='partial').count(),
        'sent': Invoice.objects.filter(status='sent').count(),
        'overdue': Invoice.objects.filter(status='overdue').count(),
        'draft': Invoice.objects.filter(status='draft').count(),
    }

    # Recent Records
    recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:6]
    recent_customers = Customer.objects.order_by('-created_at')[:5]
    recent_payments = Payment.objects.select_related('invoice', 'invoice__customer').order_by('-created_at')[:5]

    # Monthly revenue data for last 6 months (for Chart.js)
    today = timezone.now().date()
    months_labels = []
    monthly_revenues = []

    for i in range(5, -1, -1):
        # Calculate month and year
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        month_start = timezone.datetime(year, month, 1).date()
        if month == 12:
            next_month_start = timezone.datetime(year + 1, 1, 1).date()
        else:
            next_month_start = timezone.datetime(year, month + 1, 1).date()

        month_label = month_start.strftime("%b %Y")
        months_labels.append(month_label)

        month_rev = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lt=next_month_start
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        monthly_revenues.append(float(month_rev))

    # Doughnut chart status distribution: Paid, Partial, Unpaid/Pending, Overdue, Draft
    pending_total = invoice_counts['unpaid'] + invoice_counts['sent']
    status_chart_data = [
        invoice_counts['paid'],
        invoice_counts['partial'],
        pending_total,
        invoice_counts['overdue'],
        invoice_counts['draft']
    ]


    context = {
        'total_customers': total_customers,
        'active_customers': active_customers,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'low_stock_items': list(low_stock_products[:5]) + list(out_of_stock_products[:5]),
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_pending': total_pending,
        'invoice_counts': invoice_counts,
        'recent_invoices': recent_invoices,
        'recent_customers': recent_customers,
        'recent_payments': recent_payments,
        'chart_labels': json.dumps(months_labels),
        'chart_revenues': json.dumps(monthly_revenues),
        'chart_status_data': json.dumps(status_chart_data),
    }
    return render(request, 'core/dashboard.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name or user.username}! Your business account has been created.')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Please resolve the errors below.')
    else:
        form = UserRegistrationForm()

    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = UserLoginForm()

    return render(request, 'core/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out safely.')
    return redirect('core:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile details updated successfully!')
            return redirect('core:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'core/profile.html', {'form': form})
