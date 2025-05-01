from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Company, UserProfile
from .forms import RegisterForm
import tempfile
import os


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.waiting_approval_url = reverse('waiting_approval')
        self.admin_dashboard_url = '/admin-dashboard/'  # Update with your actual URL
        self.dashboard_url = '/dashboard/'  # Update with your actual URL

        # Create a test company
        self.company = Company.objects.create(
            name='Test Company',
            email='test@company.com',
            website='https://testcompany.com'
        )

        # Test user data
        self.valid_user_data = {
            'username': 'testuser',
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password1': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
            'dob': '1990-01-01',
            'role': 'team_member'
        }

        # Create a senior manager for tests that need one
        self.senior_manager = User.objects.create_user(
            username='seniormanager',
            email='manager@example.com',
            password='ManagerPass123!'
        )
        UserProfile.objects.create(
            user=self.senior_manager,
            role='senior_manager',
            company=self.company,
            is_approved=True
        )

    def test_form_validation(self):
        # Test missing required fields
        for field in ['username', 'full_name', 'email', 'password1', 'password2', 'dob', 'role']:
            data = self.valid_user_data.copy()
            del data[field]
            response = self.client.post(self.register_url, data)
            self.assertFalse(response.context['form'].is_valid())
            self.assertIn(field, response.context['form'].errors)

        # Test password mismatch - updated assertion
        data = self.valid_user_data.copy()
        data['password2'] = 'DifferentPassword123!'
        response = self.client.post(self.register_url, data)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('password2', response.context['form'].errors)
        self.assertIn("The two password fields didn’t match.", str(response.context['form'].errors['password2']))

        # Test invalid email
        data = self.valid_user_data.copy()
        data['email'] = 'notanemail'
        response = self.client.post(self.register_url, data)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('email', response.context['form'].errors)

        # Test duplicate username
        User.objects.create_user(username='existinguser', password='testpass123')
        data = self.valid_user_data.copy()
        data['username'] = 'existinguser'
        response = self.client.post(self.register_url, data)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('username', response.context['form'].errors)

    def test_successful_senior_manager_registration(self):
        # Delete the existing senior manager first
        UserProfile.objects.filter(role='senior_manager').delete()
        User.objects.filter(username='seniormanager').delete()

        data = self.valid_user_data.copy()
        data.update({
            'username': 'newmanager',
            'email': 'newmanager@example.com',
            'role': 'senior_manager'
        })

        response = self.client.post(self.register_url, data)

        # Check user was created
        new_user = User.objects.get(username='newmanager')
        profile = UserProfile.objects.get(user=new_user)

        # Senior manager should be auto-approved
        self.assertTrue(profile.is_approved)
        # Should redirect to admin dashboard (using the full URL path)
        self.assertRedirects(response, self.admin_dashboard_url, status_code=302)

    def test_waiting_approval_page(self):
        # Create an unapproved user and log in
        user = User.objects.create_user(username='unapproved', password='testpass123')
        UserProfile.objects.create(
            user=user,
            role='team_member',
            company=self.company,
            is_approved=False
        )
        self.client.login(username='unapproved', password='testpass123')

        response = self.client.get(self.waiting_approval_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/waiting_approval.html')
        self.assertEqual(response.context['user'], user)

        # Test that approved users are redirected away
        user.profile.is_approved = True
        user.profile.save()
        response = self.client.get(self.waiting_approval_url)
        self.assertRedirects(response, self.dashboard_url, status_code=302)

    def test_authenticated_user_redirect(self):
        # Log in as the senior manager
        self.client.login(username='seniormanager', password='ManagerPass123!')

        response = self.client.get(self.register_url)
        # Should redirect to admin dashboard (using the full URL path)
        self.assertRedirects(response, self.admin_dashboard_url, status_code=302)

        # Log in as a team member
        team_member = User.objects.create_user(username='teammember', password='testpass123')
        UserProfile.objects.create(
            user=team_member,
            role='team_member',
            company=self.company,
            is_approved=True
        )
        self.client.login(username='teammember', password='testpass123')

        response = self.client.get(self.register_url)
        # Should redirect to regular dashboard (using the full URL path)
        self.assertRedirects(response, self.dashboard_url, status_code=302)

    def test_password_validation(self):
        weak_passwords = [
            ('short', 'This password is too short. It must contain at least 8 characters.'),
            ('password', 'This password is too common.'),
            ('12345678', 'This password is entirely numeric.'),
            ('testuser', 'The password is too similar to the username.'),
        ]

        for password, expected_error in weak_passwords:
            data = self.valid_user_data.copy()
            data['password1'] = password
            data['password2'] = password
            response = self.client.post(self.register_url, data)
            self.assertFalse(response.context['form'].is_valid())
            self.assertIn('password2', response.context['form'].errors)
            self.assertIn(expected_error, str(response.context['form'].errors['password2']))
