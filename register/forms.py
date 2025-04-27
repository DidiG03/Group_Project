from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Company, UserProfile

class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('admin', 'Admin - Create a new company'),
        ('employee', 'Employee - Join an existing company'),
    ]
    
    username = forms.CharField(max_length=150, required=True, help_text="Required. 150 characters or fewer.")
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=100, required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, widget=forms.RadioSelect)
    company_name = forms.CharField(max_length=100, required=True)
    company_code = forms.CharField(max_length=10, required=False)
    dob = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'password1', 'password2', 'dob', 'role', 'company_name', 'company_code']
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company_code = cleaned_data.get('company_code')
        company_name = cleaned_data.get('company_name')
        
        if role == 'employee':
            if not company_code:
                self.add_error('company_code', 'Company access code is required for employees')
            else:
                # Verify the company code is valid
                try:
                    company = Company.objects.get(name=company_name, access_code=company_code)
                except Company.DoesNotExist:
                    self.add_error('company_code', 'Invalid company name or access code')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Split full name into first name and last name
        name_parts = self.cleaned_data['full_name'].split(' ', 1)
        user.first_name = name_parts[0]
        if len(name_parts) > 1:
            user.last_name = name_parts[1]
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']  # Use provided username
        
        if commit:
            user.save()
            
            role = self.cleaned_data['role']
            
            if role == 'admin':
                # Create a new company for admin users
                company = Company.objects.create(
                    name=self.cleaned_data['company_name'],
                    created_by=user
                )
                
                # Create a user profile - admins are automatically approved
                UserProfile.objects.create(
                    user=user,
                    role=role,
                    company=company,
                    is_approved=True  # Auto-approve admin users
                )
            else:
                # For employees, use the existing company
                company = Company.objects.get(
                    name=self.cleaned_data['company_name'],
                    access_code=self.cleaned_data['company_code']
                )
                
                # Create a user profile - employees need approval
                UserProfile.objects.create(
                    user=user,
                    role=role,
                    company=company
                    # is_approved defaults to False for employees
                )
            
        return user