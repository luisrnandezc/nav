# Generated by Django 5.2.3 on 2025-06-27 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fms', '0009_alter_flightevaluation0_100_course_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='flightlog',
            name='evaluation_id',
            field=models.PositiveIntegerField(help_text='ID única de evaluación asociada', null=True, verbose_name='ID de evaluación'),
        ),
        migrations.AddField(
            model_name='simulatorlog',
            name='evaluation_id',
            field=models.PositiveIntegerField(help_text='ID única de evaluación asociada', null=True, verbose_name='ID de evaluación'),
        ),
    ]
