# Generated by Django 5.2 on 2025-04-13 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0005_currency_is_default_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='cancellation_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('cancelled', 'Cancelled')], default='active', max_length=10),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='renewal_period',
            field=models.CharField(choices=[('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly'), ('biennial', 'Biennial')], default='monthly', max_length=10),
        ),
    ]
