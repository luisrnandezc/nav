# Generated by Django 5.0.6 on 2025-04-04 18:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0004_remove_courseedition_end_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subjectedition',
            options={'ordering': ['subject_type'], 'verbose_name': 'Subject Edition', 'verbose_name_plural': 'Subject Editions'},
        ),
        migrations.RemoveField(
            model_name='subjectedition',
            name='course_edition',
        ),
    ]
