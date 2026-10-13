from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Customer


class CustomerModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()
        self.client.login(username='testuser', password='password123')

        self.customer = Customer.objects.create(
            name="Aman Sharma",
            email="aman@example.com",
            phone="9876543210",
            company="Tech Solutions",
            city="Mumbai",
            state="Maharashtra",
            is_active=True
        )

    def test_customer_creation(self):
        self.assertEqual(str(self.customer), "Aman Sharma (Tech Solutions)")
        self.assertTrue(self.customer.is_active)

    def test_customer_list_view(self):
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aman Sharma")

    def test_customer_create_view(self):
        response = self.client.post(reverse('customers:customer_create'), {
            'name': 'Rahul Verma',
            'email': 'rahul@example.com',
            'phone': '9123456780',
            'company': 'Verma Enterprises',
            'city': 'Delhi',
            'state': 'Delhi',
            'is_active': True,
        })
        self.assertEqual(Customer.objects.count(), 2)
        self.assertEqual(response.status_code, 302)

    def test_customer_detail_view(self):
        response = self.client.get(reverse('customers:customer_detail', kwargs={'pk': self.customer.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aman Sharma")
        self.assertContains(response, "Tech Solutions")

    def test_customer_update_view(self):
        response = self.client.post(reverse('customers:customer_update', kwargs={'pk': self.customer.pk}), {
            'name': 'Aman Sharma Updated',
            'email': 'aman@example.com',
            'phone': '9999999999',
            'company': 'Tech Global',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, 'Aman Sharma Updated')
        self.assertEqual(self.customer.company, 'Tech Global')

    def test_customer_delete_view(self):
        response = self.client.post(reverse('customers:customer_delete', kwargs={'pk': self.customer.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk).exists())

    def test_customer_search_and_filter(self):
        # Search query
        response = self.client.get(reverse('customers:customer_list') + '?q=Mumbai')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aman Sharma")

        # Inactive filter
        response = self.client.get(reverse('customers:customer_list') + '?status=inactive')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Aman Sharma")

    def test_customer_validation_empty_name(self):
        response = self.client.post(reverse('customers:customer_create'), {
            'name': '   ',
            'email': 'invalid@test.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customer.objects.filter(email='invalid@test.com').exists())

