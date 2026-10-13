from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from customers.models import Customer
from products.models import Product
from sales.models import Invoice, InvoiceItem, Payment


class SalesWorkflowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testadmin', password='password123')
        self.client = Client()
        self.client.login(username='testadmin', password='password123')

        self.customer = Customer.objects.create(
            name="Rahul Sharma",
            email="rahul@example.com",
            company="Tech Corp"
        )

        self.product = Product.objects.create(
            name="Cloud Server Setup",
            sku="SRV-CLOUD",
            product_type="service",
            unit_price=Decimal('5000.00'),
            cost_price=Decimal('1000.00'),
            stock_quantity=0
        )

        self.invoice = Invoice.objects.create(
            invoice_number="INV-2026-TEST",
            customer=self.customer,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=15),
            status="draft",
            tax_rate=Decimal('18.00'),
            discount=Decimal('500.00')
        )

        self.item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            description="Cloud Setup Service",
            quantity=Decimal('2.00'),
            unit_price=Decimal('5000.00')
        )
        self.invoice.calculate_totals()

    def test_invoice_calculations(self):
        # Subtotal: 2 * 5000 = 10000
        # Tax: 18% of 10000 = 1800
        # Discount: 500
        # Total: 10000 + 1800 - 500 = 11300
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.subtotal, Decimal('10000.00'))
        self.assertEqual(self.invoice.tax_amount, Decimal('1800.00'))
        self.assertEqual(self.invoice.total_amount, Decimal('11300.00'))
        self.assertEqual(self.invoice.balance_due, Decimal('11300.00'))

    def test_payment_and_auto_status_update(self):
        # Record partial payment
        payment = Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal('5000.00'),
            payment_method='upi',
            reference_number='UPI123456789'
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.paid_amount, Decimal('5000.00'))
        self.assertEqual(self.invoice.balance_due, Decimal('6300.00'))
        self.assertEqual(self.invoice.status, 'partial')

        # Pay remaining balance
        Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal('6300.00'),
            payment_method='bank_transfer',
            reference_number='TXN987654'
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.paid_amount, Decimal('11300.00'))
        self.assertEqual(self.invoice.balance_due, Decimal('0.00'))
        self.assertEqual(self.invoice.status, 'paid')

    def test_payment_validation_overpayment_rejected(self):
        """Payments exceeding the balance due must be rejected on server"""
        from django.core.exceptions import ValidationError
        # Balance due is 11300.00. Trying to pay 15000.00 must raise ValidationError
        with self.assertRaises(ValidationError):
            payment = Payment(
                invoice=self.invoice,
                amount=Decimal('15000.00'),
                payment_method='cash'
            )
            payment.clean()

    def test_payment_validation_zero_or_negative_rejected(self):
        """Payments with zero or negative amounts must be rejected"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            payment = Payment(
                invoice=self.invoice,
                amount=Decimal('0.00'),
                payment_method='cash'
            )
            payment.clean()

        with self.assertRaises(ValidationError):
            payment = Payment(
                invoice=self.invoice,
                amount=Decimal('-100.00'),
                payment_method='cash'
            )
            payment.clean()

    def test_invoice_create_view_with_items(self):
        response = self.client.post(reverse('sales:invoice_create'), {
            'invoice_number': 'INV-TEST-NEW-01',
            'customer': self.customer.pk,
            'issue_date': timezone.now().date(),
            'due_date': timezone.now().date() + timezone.timedelta(days=15),
            'status': 'draft',
            'tax_rate': '10.00',
            'discount': '100.00',
            'item_product[]': [self.product.pk],
            'item_description[]': ['Test Item Creation'],
            'item_quantity[]': ['2.00'],
            'item_price[]': ['1000.00'],
        })
        self.assertEqual(response.status_code, 302)
        new_inv = Invoice.objects.filter(invoice_number='INV-TEST-NEW-01').first()
        self.assertIsNotNone(new_inv)
        self.assertEqual(new_inv.items.count(), 1)
        # Subtotal: 2 * 1000 = 2000; Tax 10%: 200; Discount: 100 => Total: 2100
        self.assertEqual(new_inv.total_amount, Decimal('2100.00'))

    def test_invoice_create_zero_items_rejected(self):
        response = self.client.post(reverse('sales:invoice_create'), {
            'invoice_number': 'INV-EMPTY-TEST',
            'customer': self.customer.pk,
            'issue_date': timezone.now().date(),
            'due_date': timezone.now().date() + timezone.timedelta(days=15),
            'status': 'draft',
            'item_description[]': [],
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Invoice.objects.filter(invoice_number='INV-EMPTY-TEST').exists())

    def test_invoice_create_invalid_quantity_rejected(self):
        response = self.client.post(reverse('sales:invoice_create'), {
            'invoice_number': 'INV-NEG-QTY',
            'customer': self.customer.pk,
            'issue_date': timezone.now().date(),
            'due_date': timezone.now().date() + timezone.timedelta(days=15),
            'status': 'draft',
            'item_description[]': ['Invalid item'],
            'item_quantity[]': ['-5.00'],
            'item_price[]': ['100.00'],
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Invoice.objects.filter(invoice_number='INV-NEG-QTY').exists())

    def test_invoice_printable_view(self):
        response = self.client.get(reverse('sales:invoice_print', kwargs={'pk': self.invoice.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.invoice.invoice_number)
        self.assertContains(response, "Rahul Sharma")
        self.assertContains(response, "Print / Save as PDF")

    def test_unique_invoice_number_generation(self):
        from sales.models import generate_unique_invoice_number
        inv_no_1 = generate_unique_invoice_number()
        self.assertTrue(inv_no_1.startswith('INV-'))
        # Create an invoice with this number
        Invoice.objects.create(
            invoice_number=inv_no_1,
            customer=self.customer,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=10),
        )
        inv_no_2 = generate_unique_invoice_number()
        self.assertNotEqual(inv_no_1, inv_no_2)

