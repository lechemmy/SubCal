"""
Mixins for the subscriptions app to handle user-specific data and permissions.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


class UserDataMixin(LoginRequiredMixin):
    """
    Mixin to filter queryset by current user.

    This mixin ensures that users can only see their own data.
    """

    def get_queryset(self):
        """
        Filter the queryset to include only objects owned by the current user.
        """
        queryset = super().get_queryset()

        # Check if the model has a user field
        if hasattr(queryset.model, 'user'):
            # Since we don't have global items anymore, just filter by user
            return queryset.filter(user=self.request.user)

        # If the model doesn't have a user field, return the original queryset
        return queryset


class ObjectAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check if user has access to a specific object.

    This mixin ensures that users can only access objects they own.
    """

    def test_func(self):
        """
        Test if the current user has access to the object.

        Returns:
            bool: True if the user has access, False otherwise.
        """
        obj = self.get_object()

        # Admin users can access everything
        if hasattr(self.request.user, 'profile') and self.request.user.profile.is_admin:
            return True

        # Check if the object has a user field
        if hasattr(obj, 'user'):
            # User can access their own objects
            if obj.user == self.request.user:
                return True

        return False

    def handle_no_permission(self):
        """
        Handle the case where the user doesn't have permission.

        Raises:
            PermissionDenied: If the user doesn't have permission.
        """
        raise PermissionDenied("You don't have permission to access this object.")


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to restrict access to admin users only.

    This mixin ensures that only users with the is_admin flag can access the view.
    """

    def test_func(self):
        """
        Test if the current user is an admin.

        Returns:
            bool: True if the user is an admin, False otherwise.
        """
        return hasattr(self.request.user, 'profile') and self.request.user.profile.is_admin
