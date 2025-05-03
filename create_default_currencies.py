import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SubCal.settings')
django.setup()

from subscriptions.models import Currency
from django.contrib.auth import get_user_model

User = get_user_model()

# Define the default currencies
default_currencies = [
    {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'is_default': True},
    {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'is_default': False},
    {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'is_default': False},
]

# Get the admin user (should have been created by create_default_categories.py)
try:
    admin_user = User.objects.get(username='admin')
except User.DoesNotExist:
    # Create admin user if it doesn't exist
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin'
    )
    print("Created default admin user.")

# Create the currencies if they don't exist
for currency_data in default_currencies:
    Currency.objects.get_or_create(
        code=currency_data['code'],
        user=admin_user,
        defaults={
            'name': currency_data['name'],
            'symbol': currency_data['symbol'],
            'is_default': currency_data['is_default'],
            'user': admin_user
        }
    )

print(f"Created {len(default_currencies)} default currencies.")
