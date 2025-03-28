# Generated by Django 5.1.3 on 2024-12-12 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_instructor_instructor_email_staff_staff_email_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instructor',
            name='instructor_email',
            field=models.EmailField(default=None, max_length=254, unique=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='staff',
            name='staff_email',
            field=models.EmailField(default=None, max_length=254, unique=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='student',
            name='student_email',
            field=models.EmailField(default=None, max_length=254, unique=True, verbose_name='Email'),
        ),
    ]
