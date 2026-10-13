from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class CoreAuthAndDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='businessowner',
            email='owner@biz.com',
            password='secretpassword123'
        )

    def test_login_and_dashboard_access(self):
        # Unauthenticated user should be redirected to login
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)

        # Authenticate
        login_success = self.client.login(username='businessowner', password='secretpassword123')
        self.assertTrue(login_success)

        # Access dashboard
        dashboard_response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, "Dashboard")

    def test_user_registration(self):
        response = self.client.post(reverse('core:register'), {
            'first_name': 'New',
            'last_name': 'Owner',
            'username': 'newowner',
            'email': 'newowner@test.com',
            'password': 'password456',
            'confirm_password': 'password456',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newowner').exists())

    def test_invalid_login(self):
        response = self.client.post(reverse('core:login'), {
            'username': 'businessowner',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_logout(self):
        self.client.login(username='businessowner', password='secretpassword123')
        response = self.client.get(reverse('core:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:login'))

    def test_profile_update(self):
        self.client.login(username='businessowner', password='secretpassword123')
        response = self.client.post(reverse('core:profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@biz.com',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.email, 'updated@biz.com')

