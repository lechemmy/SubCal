# Generated by Django 5.1.7 on 2025-03-27 23:27

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('renewal_period', models.CharField(choices=[('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], default='monthly', max_length=10)),
                ('start_date', models.DateField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
