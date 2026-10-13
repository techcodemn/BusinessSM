from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import datetime

from customers.models import Customer
from products.models import Product
from sales.models import Invoice, InvoiceItem, Payment


class Command(BaseCommand):
    help = 'Seeds initial demo business data for Business Management System'

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample business data...")

        # 1. Create default admin superuser if not exists
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser('admin', 'admin@businessms.local', 'admin123')
            admin_user.first_name = "Admin"
            admin_user.last_name = "Manager"
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Superuser: admin / admin123"))

        # 2. Create sample customers
        c1, _ = Customer.objects.get_or_create(
            email="rajesh@apextech.in",
            defaults={
                'name': "Rajesh Sharma",
                'company': "Apex Technologies Ltd",
                'phone': "+91 98201 12345",
                'address': "402 Nariman Point",
                'city': "Mumbai",
                'state': "Maharashtra",
                'postal_code': "400021",
                'notes': "Enterprise client, annual retainer."
            }
        )

        c2, _ = Customer.objects.get_or_create(
            email="priya@zenithdigital.com",
            defaults={
                'name': "Priya Patel",
                'company': "Zenith Digital Media",
                'phone': "+91 97123 45678",
                'address': "B-12 Cyber City",
                'city': "Gurugram",
                'state': "Haryana",
                'postal_code': "122002",
                'notes': "Monthly marketing and tech consulting."
            }
        )

        c3, _ = Customer.objects.get_or_create(
            email="amit@globalretail.in",
            defaults={
                'name': "Amit Verma",
                'company': "Global Retail Hub",
                'phone': "+91 94150 98765",
                'address': "Plot 55, Indiranagar",
                'city': "Bengaluru",
                'state': "Karnataka",
                'postal_code': "560038"
            }
        )

        # 3. Create sample products & services
        p1, _ = Product.objects.get_or_create(
            sku="SRV-DEV-01",
            defaults={
                'name': "Custom Software Development",
                'product_type': 'service',
                'category': "Engineering",
                'unit_price': Decimal('45000.00'),
                'cost_price': Decimal('15000.00'),
                'stock_quantity': 0,
                'description': "Full stack web & cloud backend architecture engineering."
            }
        )

        p2, _ = Product.objects.get_or_create(
            sku="SRV-CONS-02",
            defaults={
                'name': "Digital Marketing & SEO Audit",
                'product_type': 'service',
                'category': "Marketing",
                'unit_price': Decimal('18000.00'),
                'cost_price': Decimal('4000.00'),
                'stock_quantity': 0,
                'description': "Complete organic visibility and brand optimization package."
            }
        )

        p3, _ = Product.objects.get_or_create(
            sku="PRD-ROUTER-X",
            defaults={
                'name': "Enterprise Dual-Band Router",
                'product_type': 'product',
                'category': "Hardware",
                'unit_price': Decimal('6500.00'),
                'cost_price': Decimal('4200.00'),
                'stock_quantity': 18,
                'description': "Gigabit WiFi 6 Router with hardware VPN firewall."
            }
        )

        p4, _ = Product.objects.get_or_create(
            sku="PRD-BACKUP-DRV",
            defaults={
                'name': "2TB SSD Encrypted External Drive",
                'product_type': 'product',
                'category': "Storage",
                'unit_price': Decimal('9200.00'),
                'cost_price': Decimal('6800.00'),
                'stock_quantity': 3,  # Low stock indicator
                'description': "Military grade AES-256 hardware encrypted backup drive."
            }
        )

        # 4. Create sample invoices
        today = timezone.now().date()

        inv1, created1 = Invoice.objects.get_or_create(
            invoice_number="INV-2026-0001",
            defaults={
                'customer': c1,
                'issue_date': today - datetime.timedelta(days=25),
                'due_date': today - datetime.timedelta(days=10),
                'status': 'paid',
                'tax_rate': Decimal('18.00'),
                'discount': Decimal('1000.00')
            }
        )
        if created1:
            InvoiceItem.objects.create(
                invoice=inv1,
                product=p1,
                description="Custom Software Development (Phase 1)",
                quantity=Decimal('1.00'),
                unit_price=Decimal('45000.00')
            )
            inv1.calculate_totals()
            # Full payment
            Payment.objects.create(
                invoice=inv1,
                payment_date=today - datetime.timedelta(days=12),
                amount=inv1.total_amount,
                payment_method='bank_transfer',
                reference_number='NEFT-APEX-8902',
                notes='Full settlement received via NEFT.'
            )

        inv2, created2 = Invoice.objects.get_or_create(
            invoice_number="INV-2026-0002",
            defaults={
                'customer': c2,
                'issue_date': today - datetime.timedelta(days=10),
                'due_date': today + datetime.timedelta(days=5),
                'status': 'partial',
                'tax_rate': Decimal('18.00'),
                'discount': Decimal('500.00')
            }
        )
        if created2:
            InvoiceItem.objects.create(
                invoice=inv2,
                product=p2,
                description="Digital Marketing & SEO Audit",
                quantity=Decimal('1.00'),
                unit_price=Decimal('18000.00')
            )
            InvoiceItem.objects.create(
                invoice=inv2,
                product=p3,
                description="Enterprise Dual-Band Router",
                quantity=Decimal('2.00'),
                unit_price=Decimal('6500.00')
            )
            inv2.calculate_totals()
            # Partial payment
            Payment.objects.create(
                invoice=inv2,
                payment_date=today - datetime.timedelta(days=3),
                amount=Decimal('15000.00'),
                payment_method='upi',
                reference_number='UPI-ZENITH-4401',
                notes='50% advance payment via UPI'
            )

        inv3, created3 = Invoice.objects.get_or_create(
            invoice_number="INV-2026-0003",
            defaults={
                'customer': c3,
                'issue_date': today - datetime.timedelta(days=2),
                'due_date': today + datetime.timedelta(days=13),
                'status': 'sent',
                'tax_rate': Decimal('18.00'),
                'discount': Decimal('0.00')
            }
        )
        if created3:
            InvoiceItem.objects.create(
                invoice=inv3,
                product=p4,
                description="2TB SSD Encrypted External Drive",
                quantity=Decimal('3.00'),
                unit_price=Decimal('9200.00')
            )
            inv3.calculate_totals()

        self.stdout.write(self.style.SUCCESS("Sample business data seeded successfully!"))
