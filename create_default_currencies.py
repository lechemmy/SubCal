import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SubCal.settings')
django.setup()

from subscriptions.models import Currency

# Define the default currencies
default_currencies = [
    {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'is_default': True},
    {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'is_default': False},
    {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'is_default': False},
]

# Create the currencies if they don't exist
for currency_data in default_currencies:
    Currency.objects.get_or_create(
        code=currency_data['code'],
        defaults={
            'name': currency_data['name'],
            'symbol': currency_data['symbol'],
            'is_default': currency_data['is_default']
        }
    )

print(f"Created {len(default_currencies)} default currencies.")
