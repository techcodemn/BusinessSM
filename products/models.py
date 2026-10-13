from django.db import models


class Product(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('product', 'Physical Product'),
        ('service', 'Service / Consulting'),
    ]

    name = models.CharField(max_length=150, verbose_name="Item Name")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU / Item Code")
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default='product',
        verbose_name="Item Type"
    )
    category = models.CharField(max_length=100, default='General', verbose_name="Category")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Selling Price (₹/$)")
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Cost Price (₹/$)"
    )
    stock_quantity = models.IntegerField(
        default=0,
        verbose_name="Stock Quantity",
        help_text="Stock in inventory (Enter 0 or leave for Services)"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Product / Service"
        verbose_name_plural = "Products & Services"

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_service(self):
        return self.product_type == 'service'

    @property
    def is_low_stock(self):
        return self.product_type == 'product' and self.stock_quantity <= 5

    @property
    def is_out_of_stock(self):
        return self.product_type == 'product' and self.stock_quantity <= 0

    @property
    def profit_margin(self):
        return self.unit_price - self.cost_price

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        from decimal import Decimal
        if self.unit_price is not None and self.unit_price < Decimal('0.00'):
            raise ValidationError({'unit_price': 'Selling price cannot be negative.'})
        if self.cost_price is not None and self.cost_price < Decimal('0.00'):
            raise ValidationError({'cost_price': 'Cost price cannot be negative.'})
        if self.product_type == 'product' and self.stock_quantity is not None and self.stock_quantity < 0:
            raise ValidationError({'stock_quantity': 'Stock quantity cannot be negative for physical products.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
