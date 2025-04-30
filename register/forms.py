from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Company, UserProfile

class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('senior_manager', 'Senior Manager'),
        ('team_member', 'Team Member'),
    ]
    
    username = forms.CharField(max_length=150, required=True, help_text="Required. 150 characters or fewer.")
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=100, required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, widget=forms.RadioSelect)
    dob = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'password1', 'password2', 'dob', 'role']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Split full name into first name and last name
        name_parts = self.cleaned_data['full_name'].split(' ', 1)
        user.first_name = name_parts[0]
        if len(name_parts) > 1:
            user.last_name = name_parts[1]
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        
        if commit:
            user.save()
            
            # Get the role from the form
            role = self.cleaned_data.get('role')
            
            # Get the default company - create it if it doesn't exist
            try:
                company = Company.objects.first()
                if not company:
                    company = Company.objects.create(
                        name='Sky Group',
                        email='info@skygroup.com',
                        website='https://skygroup.com'
                    )
            except Company.DoesNotExist:
                company = Company.objects.create(
                    name='Sky Group',
                    email='info@skygroup.com',
                    website='https://skygroup.com'
                )
            
            # Create a user profile
            # Only senior managers are auto-approved
            UserProfile.objects.create(
                user=user,
                role=role,
                company=company,
                is_approved=(role == 'senior_manager')
            )
            
        return user

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == 'senior_manager':
            if UserProfile.objects.filter(role='senior_manager').exists():
                raise forms.ValidationError('A senior manager already exists. Only one senior manager is allowed.')
        return cleaned_data