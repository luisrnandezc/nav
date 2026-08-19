from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0043_studentprofile_ap_exp_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='staffprofile',
            options={
                'ordering': ['user__national_id'],
                'permissions': [
                    ('can_confirm_transactions', 'Can confirm transactions'),
                    ('can_manage_transactions', 'Can manage transactions'),
                    ('can_manage_sms', 'Can manage SMS'),
                    ('can_view_user_stats', 'Can view user statistics'),
                    ('can_update_aura_reviews', 'Can update AURA reviews'),
                    ('can_view_production', 'Can view production reports'),
                ],
                'verbose_name': 'Staff',
                'verbose_name_plural': 'Staff',
            },
        ),
    ]
