from django.db import models
from django.contrib.auth.models import User
import random
import string

def generate_access_code():
    """Generate a random 8-character access code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(8))

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="company")
    created_at = models.DateTimeField(auto_now_add=True)
    access_code = models.CharField(max_length=10, default=generate_access_code, unique=True, 
                                  help_text="Code for employees to join company")
    
    class Meta:
        verbose_name_plural = "Companies"
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employee'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="employees", null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    department = models.ForeignKey('main.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    team = models.ForeignKey('main.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    is_approved = models.BooleanField(default=False, help_text="Whether this user is approved by admin")
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile ({self.role})"
