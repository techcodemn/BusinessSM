from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Product


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()
        self.client.login(username='testuser', password='password123')

        self.product = Product.objects.create(
            name="Laptop Stand Pro",
            sku="LTP-001",
            product_type="product",
            category="Accessories",
            unit_price=1200.00,
            cost_price=800.00,
            stock_quantity=15,
            is_active=True
        )

        self.service = Product.objects.create(
            name="Web Consultation",
            sku="SRV-001",
            product_type="service",
            category="Consulting",
            unit_price=5000.00,
            cost_price=0.00,
            stock_quantity=0,
            is_active=True
        )

    def test_product_properties(self):
        self.assertEqual(str(self.product), "Laptop Stand Pro (LTP-001)")
        self.assertEqual(self.product.profit_margin, 400.00)
        self.assertFalse(self.product.is_low_stock)
        self.assertTrue(self.service.is_service)

    def test_product_list_view(self):
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laptop Stand Pro")

    def test_product_create_view(self):
        response = self.client.post(reverse('products:product_create'), {
            'name': 'Wireless Mouse',
            'sku': 'MSE-002',
            'product_type': 'product',
            'category': 'Electronics',
            'unit_price': '450.00',
            'cost_price': '250.00',
            'stock_quantity': '30',
            'is_active': True,
        })
        self.assertEqual(Product.objects.count(), 3)
        self.assertEqual(response.status_code, 302)

    def test_product_detail_view(self):
        response = self.client.get(reverse('products:product_detail', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laptop Stand Pro")
        self.assertContains(response, "LTP-001")

    def test_product_update_view(self):
        response = self.client.post(reverse('products:product_update', kwargs={'pk': self.product.pk}), {
            'name': 'Laptop Stand Pro Ultra',
            'sku': 'LTP-001',
            'product_type': 'product',
            'category': 'Accessories',
            'unit_price': '1500.00',
            'cost_price': '800.00',
            'stock_quantity': '20',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Laptop Stand Pro Ultra')
        self.assertEqual(self.product.unit_price, 1500.00)

    def test_product_delete_view(self):
        response = self.client.post(reverse('products:product_delete', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_product_validation_negative_price(self):
        response = self.client.post(reverse('products:product_create'), {
            'name': 'Invalid Item',
            'sku': 'INV-999',
            'product_type': 'product',
            'unit_price': '-50.00',
            'cost_price': '10.00',
            'stock_quantity': '10',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(sku='INV-999').exists())

    def test_product_validation_negative_stock(self):
        response = self.client.post(reverse('products:product_create'), {
            'name': 'Invalid Stock Item',
            'sku': 'INV-888',
            'product_type': 'product',
            'unit_price': '50.00',
            'cost_price': '10.00',
            'stock_quantity': '-5',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(sku='INV-888').exists())

    def test_low_stock_filters(self):
        # Create a low-stock product
        Product.objects.create(
            name="Low Stock Item",
            sku="LOW-001",
            product_type="product",
            unit_price=100.00,
            stock_quantity=3,
            is_active=True
        )
        response = self.client.get(reverse('products:product_list') + '?stock=low')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Low Stock Item")

