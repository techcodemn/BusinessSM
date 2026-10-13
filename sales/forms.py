from django import forms
from django.utils import timezone
from .models import Invoice, InvoiceItem, Payment
from customers.models import Customer


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'customer', 'issue_date', 'due_date',
            'status', 'tax_rate', 'discount', 'notes', 'terms'
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'INV-2026-0001',
                'required': True
            }),
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Thanks for your business!'
            }),
            'terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active customers in dropdown
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
        if not self.instance.pk:
            # Set default due date to 15 days from now
            self.fields['due_date'].initial = timezone.now().date() + timezone.timedelta(days=15)
            self.fields['issue_date'].initial = timezone.now().date()

    def clean_tax_rate(self):
        tax = self.cleaned_data.get('tax_rate')
        if tax is not None and (tax < 0 or tax > 100):
            raise forms.ValidationError("Tax rate must be between 0% and 100%.")
        return tax

    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount is not None and discount < 0:
            raise forms.ValidationError("Discount cannot be negative.")
        return discount

    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        due_date = cleaned_data.get('due_date')
        if issue_date and due_date and due_date < issue_date:
            self.add_error('due_date', "Due date cannot be earlier than the issue date.")
        return cleaned_data


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'payment_date', 'amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'required': True}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UPI ID / Cheque # / Ref'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Payment notes...'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        invoice = cleaned_data.get('invoice')
        amount = cleaned_data.get('amount')
        if invoice and amount is not None and amount > 0:
            # If editing existing payment, allow up to balance_due + existing payment amount
            current_paid_from_this = 0
            if self.instance and self.instance.pk:
                current_paid_from_this = self.instance.amount
            max_allowed = invoice.balance_due + current_paid_from_this
            if amount > max_allowed:
                self.add_error(
                    'amount',
                    f"Payment amount (₹{amount}) cannot exceed the outstanding balance of ₹{max_allowed}."
                )
        return cleaned_data

