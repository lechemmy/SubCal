import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SubCal.settings')
django.setup()

from subscriptions.models import Category
from django.contrib.auth import get_user_model

User = get_user_model()

# Define the default categories
default_categories = [
    'Entertainment',
    'Hosting',
    'Cloud',
    'Utilities'
]

# Get or create a default admin user for system-wide defaults
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'is_staff': True,
        'is_superuser': True
    }
)

if created:
    admin_user.set_password('admin')  # Set a default password
    admin_user.save()
    print("Created default admin user.")

# Create the categories if they don't exist, assigning them to the admin user
for category_name in default_categories:
    Category.objects.get_or_create(name=category_name, user=admin_user)

print(f"Created {len(default_categories)} default categories.")
