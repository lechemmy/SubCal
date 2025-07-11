# Generated by Django 5.2 on 2025-05-02 15:06

from django.db import migrations


def assign_subscriptions_to_users(apps, schema_editor):
    """
    Assign existing subscriptions to users.
    If no users exist, create an admin user and assign all subscriptions to them.
    """
    User = apps.get_model('auth', 'User')
    Subscription = apps.get_model('subscriptions', 'Subscription')

    # Get all subscriptions without a user
    subscriptions_without_user = Subscription.objects.filter(user__isnull=True)

    if subscriptions_without_user.exists():
        # Get the first admin user, or create one if none exists
        admin_user = User.objects.filter(is_superuser=True).first()

        if not admin_user:
            # Create an admin user if none exists
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='changeme'
            )

        # Assign all subscriptions without a user to the admin user
        subscriptions_without_user.update(user=admin_user)


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0010_subscription_user'),
        ('users', '0002_userprofile_delete_user'),
    ]

    operations = [
        migrations.RunPython(assign_subscriptions_to_users),
    ]
