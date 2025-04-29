from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('register', '0010_create_default_company'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='address',
        ),
        migrations.RemoveField(
            model_name='company',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='company',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='company',
            name='access_code',
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='company',
            field=models.ForeignKey('register.Company', on_delete=models.CASCADE, related_name='employees'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(choices=[('senior_manager', 'Senior Manager'), ('team_member', 'Team Member')], default='team_member', max_length=20),
        ),
    ] 