from django.contrib import admin
from django.contrib.auth.models import User

from .models import Department, Team

# Register your models here.
admin.site.register(Department)
admin.site.register(Team)

