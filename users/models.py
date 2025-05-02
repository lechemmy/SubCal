"""
Models for the users app.
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    User profile model for SubCal.

    Extends Django's User model with additional fields and functionality
    specific to the SubCal application.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Add is_admin field to distinguish between regular users and admin users
    is_admin = models.BooleanField(
        _('admin status'),
        default=False,
        help_text=_('Designates whether the user has admin privileges.'),
    )

    # Add email_verified field for email verification functionality
    email_verified = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether the user has verified their email address.'),
    )

    # Add any additional fields needed for the application

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        """
        Return a string representation of the user profile.
        """
        return f"{self.user.username}'s profile"

    def save(self, *args, **kwargs):
        """
        Override the save method to ensure that admin users are also staff users.
        """
        if self.is_admin and not self.user.is_staff:
            self.user.is_staff = True
            self.user.save()
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile for each new User.
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the User is saved.
    """
    instance.profile.save()
