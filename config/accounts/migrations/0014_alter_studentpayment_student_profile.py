# Generated by Django 5.0.6 on 2025-05-16 00:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_remove_studentprofile_student_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentpayment',
            name='student_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='accounts.studentprofile'),
        ),
    ]
