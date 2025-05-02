"""
Signal handlers for the users app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to perform actions when a user is created.

    This can be used to create related objects or perform other actions
    when a new user is created.

    Args:
        sender: The model class that sent the signal (User)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Example: You could create a profile for the user here
        # Profile.objects.create(user=instance)

        # Create default categories for the user
        from subscriptions.models import Category, Currency

        # Create default categories for the new user
        default_categories = ["Food", "Petrol", "Computer", "Mobile", "Shopping"]

        # Create user-specific categories
        for category_name in default_categories:
            Category.objects.create(
                name=category_name,
                user=instance
            )

        # Create default currencies for the new user
        currencies_data = [
            {"code": "GBP", "name": "British Pound", "symbol": "£", "is_default": True},
            {"code": "USD", "name": "US Dollar", "symbol": "$", "is_default": False},
            {"code": "EUR", "name": "Euro", "symbol": "€", "is_default": False},
        ]

        for currency_data in currencies_data:
            Currency.objects.create(
                code=currency_data["code"],
                name=currency_data["name"],
                symbol=currency_data["symbol"],
                is_default=currency_data["is_default"],
                user=instance
            )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal handler to perform actions when a user is saved.

    This can be used to update related objects or perform other actions
    when a user is updated.

    Args:
        sender: The model class that sent the signal (User)
        instance: The actual instance being saved
        **kwargs: Additional keyword arguments
    """
    # Example: You could save the user's profile here
    # if hasattr(instance, 'profile'):
    #     instance.profile.save()

    # Ensure admin users are also staff users
    if hasattr(instance, 'profile') and instance.profile.is_admin and not instance.is_staff:
        instance.is_staff = True
        # Use update to avoid recursive signal calls
        User.objects.filter(pk=instance.pk).update(is_staff=True)
