from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from decimal import Decimal
from django.utils import timezone
from .models import Invoice, InvoiceItem, Payment, generate_unique_invoice_number
from .forms import InvoiceForm, PaymentForm
from products.models import Product


@login_required
def invoice_list(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')

    invoices = Invoice.objects.select_related('customer').all()

    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__company__icontains=query)
        )

    if status_filter != 'all' and status_filter in dict(Invoice.STATUS_CHOICES):
        invoices = invoices.filter(status=status_filter)

    # Statistics for summary header cards
    total_sales = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_collected = invoices.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0.00')
    total_pending = invoices.aggregate(Sum('balance_due'))['balance_due__sum'] or Decimal('0.00')

    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'status_choices': Invoice.STATUS_CHOICES,
        'total_sales': total_sales,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_count': invoices.count(),
    }
    return render(request, 'sales/invoice_list.html', context)


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('customer'), pk=pk)
    # Refresh totals to be accurate
    invoice.calculate_totals()
    items = invoice.items.select_related('product').all()
    payments = invoice.payments.all()
    payment_form = PaymentForm(initial={'invoice': invoice, 'amount': invoice.balance_due})

    return render(request, 'sales/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'payments': payments,
        'payment_form': payment_form,
    })


@login_required
def invoice_print(request, pk):
    """Printable invoice view optimized for paper print and clean PDF generation."""
    invoice = get_object_or_404(Invoice.objects.select_related('customer'), pk=pk)
    invoice.calculate_totals()
    items = invoice.items.select_related('product').all()
    payments = invoice.payments.all()
    return render(request, 'sales/invoice_print.html', {
        'invoice': invoice,
        'items': items,
        'payments': payments,
    })


@login_required
def invoice_create(request):
    products = Product.objects.filter(is_active=True)
    suggested_inv_no = generate_unique_invoice_number()

    if request.method == 'POST':
        form = InvoiceForm(request.POST)

        descriptions = request.POST.getlist('item_description[]')
        quantities = request.POST.getlist('item_quantity[]')
        unit_prices = request.POST.getlist('item_price[]')
        product_ids = request.POST.getlist('item_product[]')

        # Validate line items before committing
        parsed_items = []
        has_error = False

        for i in range(len(descriptions)):
            desc = descriptions[i].strip()
            if desc:
                try:
                    qty = Decimal(quantities[i]) if (i < len(quantities) and quantities[i]) else Decimal('1.00')
                except Exception:
                    messages.error(request, f'Invalid quantity for item "{desc}".')
                    has_error = True
                    break

                try:
                    price = Decimal(unit_prices[i]) if (i < len(unit_prices) and unit_prices[i]) else Decimal('0.00')
                except Exception:
                    messages.error(request, f'Invalid price for item "{desc}".')
                    has_error = True
                    break

                if qty <= Decimal('0.00'):
                    messages.error(request, f'Quantity for "{desc}" must be greater than zero.')
                    has_error = True
                    break

                if price < Decimal('0.00'):
                    messages.error(request, f'Price for "{desc}" cannot be negative.')
                    has_error = True
                    break

                prod_id = product_ids[i] if (i < len(product_ids) and product_ids[i]) else None
                prod = Product.objects.filter(id=prod_id).first() if prod_id else None

                parsed_items.append({
                    'product': prod,
                    'description': desc,
                    'quantity': qty,
                    'unit_price': price,
                })

        if not parsed_items and not has_error:
            messages.error(request, 'At least one line item is required to generate an invoice.')
            has_error = True

        if form.is_valid() and not has_error:
            invoice = form.save(commit=False)
            invoice.save()

            for item_data in parsed_items:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=item_data['product'],
                    description=item_data['description'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                )

            invoice.calculate_totals()
            messages.success(request, f'Invoice "{invoice.invoice_number}" created successfully with {len(parsed_items)} item(s)!')
            return redirect('sales:invoice_detail', pk=invoice.pk)
        else:
            if not has_error and form.errors:
                messages.error(request, 'Please correct the errors in the invoice form.')
    else:
        form = InvoiceForm(initial={'invoice_number': suggested_inv_no})

    return render(request, 'sales/invoice_form.html', {
        'form': form,
        'products': products,
        'title': 'Create New Invoice',
        'button_text': 'Generate Invoice',
    })


@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    products = Product.objects.filter(is_active=True)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)

        descriptions = request.POST.getlist('item_description[]')
        quantities = request.POST.getlist('item_quantity[]')
        unit_prices = request.POST.getlist('item_price[]')
        product_ids = request.POST.getlist('item_product[]')

        parsed_items = []
        has_error = False

        for i in range(len(descriptions)):
            desc = descriptions[i].strip()
            if desc:
                try:
                    qty = Decimal(quantities[i]) if (i < len(quantities) and quantities[i]) else Decimal('1.00')
                except Exception:
                    messages.error(request, f'Invalid quantity for item "{desc}".')
                    has_error = True
                    break

                try:
                    price = Decimal(unit_prices[i]) if (i < len(unit_prices) and unit_prices[i]) else Decimal('0.00')
                except Exception:
                    messages.error(request, f'Invalid price for item "{desc}".')
                    has_error = True
                    break

                if qty <= Decimal('0.00'):
                    messages.error(request, f'Quantity for "{desc}" must be greater than zero.')
                    has_error = True
                    break

                if price < Decimal('0.00'):
                    messages.error(request, f'Price for "{desc}" cannot be negative.')
                    has_error = True
                    break

                prod_id = product_ids[i] if (i < len(product_ids) and product_ids[i]) else None
                prod = Product.objects.filter(id=prod_id).first() if prod_id else None

                parsed_items.append({
                    'product': prod,
                    'description': desc,
                    'quantity': qty,
                    'unit_price': price,
                })

        if not parsed_items and not has_error:
            messages.error(request, 'At least one line item is required in an invoice.')
            has_error = True

        if form.is_valid() and not has_error:
            invoice = form.save()

            # Clear old items and recreate updated ones
            invoice.items.all().delete()

            for item_data in parsed_items:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=item_data['product'],
                    description=item_data['description'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                )

            invoice.calculate_totals()
            messages.success(request, f'Invoice "{invoice.invoice_number}" updated successfully!')
            return redirect('sales:invoice_detail', pk=invoice.pk)
        else:
            if not has_error and form.errors:
                messages.error(request, 'Please correct the errors in the form.')
    else:
        form = InvoiceForm(instance=invoice)

    return render(request, 'sales/invoice_form.html', {
        'form': form,
        'invoice': invoice,
        'existing_items': invoice.items.all(),
        'products': products,
        'title': f'Edit Invoice: {invoice.invoice_number}',
        'button_text': 'Update Invoice',
    })


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        inv_no = invoice.invoice_number
        invoice.delete()
        messages.success(request, f'Invoice "{inv_no}" has been deleted.')
        return redirect('sales:invoice_list')

    return render(request, 'sales/invoice_confirm_delete.html', {'invoice': invoice})


@login_required
def payment_list(request):
    query = request.GET.get('q', '').strip()
    method_filter = request.GET.get('method', 'all')

    payments = Payment.objects.select_related('invoice', 'invoice__customer').all()

    if query:
        payments = payments.filter(
            Q(reference_number__icontains=query) |
            Q(invoice__invoice_number__icontains=query) |
            Q(invoice__customer__name__icontains=query)
        )

    if method_filter != 'all' and method_filter in dict(Payment.PAYMENT_METHOD_CHOICES):
        payments = payments.filter(payment_method=method_filter)

    total_received = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

    paginator = Paginator(payments, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'method_filter': method_filter,
        'method_choices': Payment.PAYMENT_METHOD_CHOICES,
        'total_received': total_received,
        'total_count': payments.count(),
    }
    return render(request, 'sales/payment_list.html', context)


@login_required
def payment_create(request):
    invoice_id = request.GET.get('invoice_id')
    initial_data = {}
    if invoice_id:
        selected_invoice = get_object_or_404(Invoice, pk=invoice_id)
        initial_data['invoice'] = selected_invoice
        initial_data['amount'] = selected_invoice.balance_due

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                payment = form.save()
                messages.success(
                    request,
                    f'Payment of ₹{payment.amount} for {payment.invoice.invoice_number} recorded successfully!'
                )
                return redirect('sales:invoice_detail', pk=payment.invoice.pk)
            except Exception as e:
                messages.error(request, f'Error saving payment: {e}')
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, err)
    else:
        form = PaymentForm(initial=initial_data)

    return render(request, 'sales/payment_form.html', {
        'form': form,
        'title': 'Record New Payment',
        'button_text': 'Save Payment',
    })


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    invoice = payment.invoice
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment record deleted and invoice totals recalculated.')
        return redirect('sales:invoice_detail', pk=invoice.pk)

    return render(request, 'sales/payment_confirm_delete.html', {
        'payment': payment,
        'invoice': invoice
    })

