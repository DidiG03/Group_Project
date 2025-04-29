from django.db import migrations
from django.contrib.auth.models import User

def create_default_company(apps, schema_editor):
    Company = apps.get_model('register', 'Company')
    if not Company.objects.exists():
        Company.objects.create(
            name='Sky Group',
            email='info@skygroup.com',
            website='https://skygroup.com'
        )

def reverse_default_company(apps, schema_editor):
    Company = apps.get_model('register', 'Company')
    Company.objects.filter(name='Sky Group').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('register', '0009_userprofile_technical_role'),
    ]

    operations = [
        migrations.RunPython(create_default_company, reverse_default_company),
    ] 