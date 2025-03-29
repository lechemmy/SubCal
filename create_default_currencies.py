import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SubCal.settings')
django.setup()

from subscriptions.models import Currency

# Define the default currencies
default_currencies = [
    {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
    {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
    {'code': 'GBP', 'name': 'British Pound', 'symbol': '£'},
]

# Create the currencies if they don't exist
for currency_data in default_currencies:
    Currency.objects.get_or_create(
        code=currency_data['code'],
        defaults={
            'name': currency_data['name'],
            'symbol': currency_data['symbol']
        }
    )

print(f"Created {len(default_currencies)} default currencies.")
