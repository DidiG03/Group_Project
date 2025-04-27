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
    
    TECHNICAL_ROLE_CHOICES = [
        ('', 'Not Specified'),
        ('software_engineer', 'Software Engineer'),
        ('frontend_developer', 'Frontend Developer'),
        ('backend_developer', 'Backend Developer'),
        ('fullstack_developer', 'Full Stack Developer'),
        ('mobile_developer', 'Mobile Developer'),
        ('web_developer', 'Web Developer'),
        ('data_scientist', 'Data Scientist'),
        ('data_engineer', 'Data Engineer'),
        ('data_analyst', 'Data Analyst'),
        ('devops_engineer', 'DevOps Engineer'),
        ('sre', 'Site Reliability Engineer'),
        ('qa_engineer', 'QA Engineer'),
        ('test_engineer', 'Test Engineer'),
        ('ui_designer', 'UI Designer'),
        ('ux_designer', 'UX Designer'),
        ('product_manager', 'Product Manager'),
        ('project_manager', 'Project Manager'),
        ('scrum_master', 'Scrum Master'),
        ('agile_coach', 'Agile Coach'),
        ('system_administrator', 'System Administrator'),
        ('network_engineer', 'Network Engineer'),
        ('security_engineer', 'Security Engineer'),
        ('database_administrator', 'Database Administrator'),
        ('cloud_architect', 'Cloud Architect'),
        ('solutions_architect', 'Solutions Architect'),
        ('technical_lead', 'Technical Lead'),
        ('engineering_manager', 'Engineering Manager'),
        ('cto', 'CTO'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    technical_role = models.CharField(max_length=50, choices=TECHNICAL_ROLE_CHOICES, default='', blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="employees", null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    department = models.ForeignKey('main.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    teams = models.ManyToManyField('main.Team', blank=True, related_name="team_members")
    is_approved = models.BooleanField(default=False, help_text="Whether this user is approved by admin")
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile ({self.role})"
