import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SubCal.settings')
django.setup()

from subscriptions.models import Category

# Define the default categories
default_categories = [
    'Entertainment',
    'Hosting',
    'Cloud',
    'Utilities'
]

# Create the categories if they don't exist
for category_name in default_categories:
    Category.objects.get_or_create(name=category_name)

print(f"Created {len(default_categories)} default categories.")
