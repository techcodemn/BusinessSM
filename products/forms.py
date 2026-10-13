from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'product_type', 'category',
            'unit_price', 'cost_price', 'stock_quantity',
            'description', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product or Service title',
                'required': True
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. PRD-001 or SRV-101',
                'required': True
            }),
            'product_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Hardware, Software, Consulting'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'required': True
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Product specifications or service scope...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price is not None and price < 0:
            raise forms.ValidationError("Selling price cannot be negative.")
        return price

    def clean_cost_price(self):
        cost = self.cleaned_data.get('cost_price')
        if cost is not None and cost < 0:
            raise forms.ValidationError("Cost price cannot be negative.")
        return cost

    def clean_stock_quantity(self):
        stock = self.cleaned_data.get('stock_quantity')
        if stock is not None and stock < 0:
            raise forms.ValidationError("Stock quantity cannot be negative.")
        return stock

    def clean(self):
        cleaned_data = super().clean()
        product_type = cleaned_data.get('product_type')
        stock = cleaned_data.get('stock_quantity')
        if product_type == 'service' and stock is None:
            cleaned_data['stock_quantity'] = 0
        return cleaned_data
