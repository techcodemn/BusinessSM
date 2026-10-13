from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=150, verbose_name="Customer Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    phone = models.CharField(max_length=25, blank=True, verbose_name="Phone Number")
    company = models.CharField(max_length=150, blank=True, verbose_name="Company Name")
    address = models.TextField(blank=True, verbose_name="Street Address")
    city = models.CharField(max_length=100, blank=True, verbose_name="City")
    state = models.CharField(max_length=100, blank=True, verbose_name="State / Province")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="Postal / ZIP Code")
    notes = models.TextField(blank=True, verbose_name="Additional Notes")
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        if self.company:
            return f"{self.name} ({self.company})"
        return self.name

    @property
    def total_spent(self):
        """Total paid amount from all invoices"""
        total = sum(invoice.paid_amount for invoice in self.invoices.all())
        return total

    @property
    def total_invoices(self):
        return self.invoices.count()
