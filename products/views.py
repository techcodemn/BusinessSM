from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product
from .forms import ProductForm


@login_required
def product_list(request):
    query = request.GET.get('q', '').strip()
    type_filter = request.GET.get('type', 'all')
    stock_filter = request.GET.get('stock', 'all')

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__icontains=query) |
            Q(description__icontains=query)
        )

    if type_filter in ['product', 'service']:
        products = products.filter(product_type=type_filter)

    if stock_filter == 'low':
        products = products.filter(product_type='product', stock_quantity__lte=5, stock_quantity__gt=0)
    elif stock_filter == 'out':
        products = products.filter(product_type='product', stock_quantity__lte=0)

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Categories list for quick chips/filter
    categories = Product.objects.values_list('category', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'query': query,
        'type_filter': type_filter,
        'stock_filter': stock_filter,
        'categories': categories,
        'total_count': products.count(),
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})


@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Item "{product.name}" created successfully!')
            return redirect('products:product_detail', pk=product.pk)
        else:
            messages.error(request, 'Please check form errors and try again.')
    else:
        form = ProductForm()

    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Add New Product or Service',
        'button_text': 'Save Item',
    })


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Item "{product.name}" updated successfully!')
            return redirect('products:product_detail', pk=product.pk)
        else:
            messages.error(request, 'Please check form errors and try again.')
    else:
        form = ProductForm(instance=product)

    return render(request, 'products/product_form.html', {
        'form': form,
        'product': product,
        'title': f'Edit Item: {product.name}',
        'button_text': 'Update Item',
    })


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Item "{name}" has been deleted.')
        return redirect('products:product_list')

    return render(request, 'products/product_confirm_delete.html', {'product': product})
