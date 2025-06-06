# Generated by Django 5.0.6 on 2025-04-05 16:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_alter_studentpayment_confirmed_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffprofile',
            name='can_confirm_payments',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='studentpayment',
            name='confirmed_by',
            field=models.ForeignKey(blank=True, limit_choices_to={'staff_profile__can_confirm_payments': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confirmed_student_payments', to=settings.AUTH_USER_MODEL),
        ),
    ]
