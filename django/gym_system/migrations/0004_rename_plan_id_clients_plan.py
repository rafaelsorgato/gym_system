# Generated by Django 5.2.1 on 2025-05-29 19:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gym_system', '0003_plans_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clients',
            old_name='plan_id',
            new_name='plan',
        ),
    ]
