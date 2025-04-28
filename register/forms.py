from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Company, UserProfile

class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('senior_manager', 'Senior manager'),
        ('department_lead', 'Department Lead'),
        ('team_leader', 'Team Leader'),
        ('engineer', 'Engineer'),
    ]
    
    username = forms.CharField(max_length=150, required=True, help_text="Required. 150 characters or fewer.")
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=100, required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, widget=forms.RadioSelect)
    company_code = forms.CharField(max_length=10, required=False)
    dob = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'password1', 'password2', 'dob', 'role', 'company_code']
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company_code = cleaned_data.get('company_code')
        
        if company_code:
            # Only verify the code if one is provided
            try:
                # Get the company by access code only
                company = Company.objects.get(access_code=company_code)
            except Company.DoesNotExist:
                self.add_error('company_code', 'Invalid company access code')
        
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
            company_code = self.cleaned_data.get('company_code')
            
            if role == 'senior_manager' or not company_code:
                # Get or create the default company for senior managers or users without a company code
                company, created = Company.objects.get_or_create(
                    name="HealthCheck Company",  # Fixed company name
                    defaults={'created_by': user}
                )
                
                # Create a user profile
                # Senior managers are automatically approved, others based on role
                is_approved = role == 'senior_manager' or role == 'department_lead'
                
                UserProfile.objects.create(
                    user=user,
                    role=role,
                    company=company,
                    is_approved=is_approved  # Auto-approve senior managers and department leads
                )
            else:
                # For other roles with a company code, use the existing company
                company = Company.objects.get(
                    access_code=company_code
                )
                
                # Create a user profile
                # Department leads are auto-approved, others need approval
                is_approved = role == 'department_lead'
                
                UserProfile.objects.create(
                    user=user,
                    role=role,
                    company=company,
                    is_approved=is_approved
                )
            
        return user