from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import datetime


def generate_unique_invoice_number():
    """Generates a guaranteed unique sequential invoice number for the current year."""
    year = timezone.now().year
    prefix = f"INV-{year}-"
    last_invoice = Invoice.objects.filter(invoice_number__startswith=prefix).order_by('-id').first()
    next_num = 1
    if last_invoice:
        try:
            parts = last_invoice.invoice_number.split('-')
            if len(parts) >= 3:
                next_num = int(parts[-1]) + 1
        except (ValueError, IndexError):
            next_num = Invoice.objects.count() + 1

    candidate = f"{prefix}{next_num:04d}"
    while Invoice.objects.filter(invoice_number=candidate).exists():
        next_num += 1
        candidate = f"{prefix}{next_num:04d}"
    return candidate


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('unpaid', 'Unpaid'),
        ('sent', 'Sent / Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="Invoice #")
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name="Customer"
    )
    issue_date = models.DateField(default=timezone.now, verbose_name="Issue Date")
    due_date = models.DateField(verbose_name="Due Date")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Invoice Status"
    )

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Tax Rate (%)"
    )
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Discount (₹/$)")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    notes = models.TextField(blank=True, verbose_name="Client Notes")
    terms = models.TextField(
        blank=True,
        default="Payment terms: Net 15 days. Please make payment via UPI or Bank Transfer.",
        verbose_name="Terms & Conditions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-created_at']
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"

    def clean(self):
        super().clean()
        if self.tax_rate is not None and (self.tax_rate < Decimal('0.00') or self.tax_rate > Decimal('100.00')):
            raise ValidationError({'tax_rate': 'Tax rate must be between 0% and 100%.'})
        if self.discount is not None and self.discount < Decimal('0.00'):
            raise ValidationError({'discount': 'Discount amount cannot be negative.'})
        if self.issue_date and self.due_date and self.due_date < self.issue_date:
            raise ValidationError({'due_date': 'Due date cannot be before the issue date.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate subtotal, tax, grand total, paid balance, and refresh status"""
        items_subtotal = sum((item.quantity * item.unit_price for item in self.items.all()), Decimal('0.00'))
        self.subtotal = items_subtotal

        # Tax calculation
        if self.tax_rate > 0:
            self.tax_amount = (self.subtotal * self.tax_rate) / Decimal('100.00')
        else:
            self.tax_amount = Decimal('0.00')

        # Total amount after discount and tax
        self.total_amount = max(Decimal('0.00'), self.subtotal + self.tax_amount - self.discount)

        # Total payments made
        total_paid = sum((payment.amount for payment in self.payments.all()), Decimal('0.00'))
        self.paid_amount = total_paid
        self.balance_due = max(Decimal('0.00'), self.total_amount - self.paid_amount)

        # Automatically update status if not explicitly cancelled
        if self.status != 'cancelled':
            if self.balance_due <= Decimal('0.00') and self.total_amount > Decimal('0.00'):
                self.status = 'paid'
            elif self.paid_amount > Decimal('0.00'):
                self.status = 'partial'
            elif self.due_date and self.due_date < timezone.now().date() and self.balance_due > Decimal('0.00'):
                self.status = 'overdue'
            elif self.status == 'draft':
                pass
            elif self.status == 'sent':
                pass
            else:
                self.status = 'unpaid'

        Invoice.objects.filter(pk=self.pk).update(
            subtotal=self.subtotal,
            tax_amount=self.tax_amount,
            total_amount=self.total_amount,
            paid_amount=self.paid_amount,
            balance_due=self.balance_due,
            status=self.status
        )


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_items'
    )
    description = models.CharField(max_length=255, verbose_name="Description / Name")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def clean(self):
        super().clean()
        if self.quantity is not None and self.quantity <= Decimal('0.00'):
            raise ValidationError({'quantity': 'Quantity must be greater than zero.'})
        if self.unit_price is not None and self.unit_price < Decimal('0.00'):
            raise ValidationError({'unit_price': 'Unit price cannot be negative.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.unit_price})"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI / Online Transfer'),
        ('bank_transfer', 'Direct Bank Transfer / NEFT / IMPS'),
        ('credit_card', 'Credit / Debit Card'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque / Demand Draft'),
        ('other', 'Other'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(default=timezone.now, verbose_name="Payment Date")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount Paid")
    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        default='upi',
        verbose_name="Payment Method"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Transaction ID / Reference",
        help_text="UPI Ref, Cheque No, Bank Txn ID"
    )
    notes = models.TextField(blank=True, verbose_name="Payment Notes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"Payment #{self.pk} - {self.invoice.invoice_number} ({self.amount})"

    def clean(self):
        super().clean()
        if self.amount is not None:
            if self.amount <= Decimal('0.00'):
                raise ValidationError({'amount': 'Payment amount must be greater than zero.'})
            if self.invoice_id:
                current_paid_from_this = Decimal('0.00')
                if self.pk:
                    old_payment = Payment.objects.filter(pk=self.pk).first()
                    if old_payment:
                        current_paid_from_this = old_payment.amount
                available_balance = self.invoice.balance_due + current_paid_from_this
                if self.amount > available_balance:
                    raise ValidationError({'amount': f'Payment amount (₹{self.amount}) cannot exceed the outstanding balance of ₹{available_balance}.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.invoice.calculate_totals()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        super().delete(*args, **kwargs)
        invoice.calculate_totals()

