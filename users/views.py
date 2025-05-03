"""
Views for the users app.
"""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView, PasswordResetConfirmView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView

from subscriptions.mixins import AdminRequiredMixin
from .forms import (
    UserRegistrationForm, CustomAuthenticationForm, CustomPasswordChangeForm,
    CustomPasswordResetForm, CustomSetPasswordForm, UserProfileForm
)
from django.contrib.auth.models import User
from .models import UserProfile


class CustomLoginView(LoginView):
    """
    Custom login view.

    Extends Django's LoginView to use custom form and template.
    """
    form_class = CustomAuthenticationForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Return the URL to redirect to after successful login.

        If 'next' parameter is provided, redirect there.
        Otherwise, redirect to home page.
        """
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('home')


class CustomLogoutView(LogoutView):
    """
    Custom logout view.

    Extends Django's LogoutView to add custom behavior.
    """
    next_page = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        """
        Add a success message before logging out.
        """
        messages.success(request, "You have been successfully logged out.")
        return super().dispatch(request, *args, **kwargs)


class UserRegistrationView(CreateView):
    """
    View for user registration.
    """
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        """
        If the form is valid, save the user and add a success message.
        """
        response = super().form_valid(form)
        messages.success(self.request, "Your account has been created successfully. You can now log in.")
        return response

    def dispatch(self, request, *args, **kwargs):
        """
        Redirect authenticated users to home page.
        """
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """
    View for changing password.

    Extends Django's PasswordChangeView to use custom form and template.
    """
    form_class = CustomPasswordChangeForm
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        """
        If the form is valid, save the password and add a success message.
        """
        response = super().form_valid(form)
        messages.success(self.request, "Your password has been changed successfully.")
        return response


class CustomPasswordResetView(PasswordResetView):
    """
    View for resetting password.

    Extends Django's PasswordResetView to use custom form and template.
    """
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    View for confirming password reset.

    Extends Django's PasswordResetConfirmView to use custom form and template.
    """
    form_class = CustomSetPasswordForm
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class UserProfileView(LoginRequiredMixin, DetailView):
    """
    View for displaying user profile.
    """
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'user_profile'

    def get_object(self, queryset=None):
        """
        Return the current user.
        """
        return self.request.user

    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        """
        context = super().get_context_data(**kwargs)

        # Import here to avoid circular imports
        from subscriptions.models import Subscription
        from decimal import Decimal

        # Get active and cancelled subscriptions for the current user
        user = self.request.user
        context['active_subscriptions'] = Subscription.objects.filter(user=user, status='active')
        context['cancelled_subscriptions'] = Subscription.objects.filter(user=user, status='cancelled')

        # Add subscription count to user_profile
        user_profile = context['user_profile']
        user_profile.subscription_count = user.subscriptions.count()

        # Calculate monthly costs by currency
        monthly_costs = {}
        for subscription in context['active_subscriptions']:
            currency = subscription.currency
            monthly_cost = self.calculate_monthly_cost(subscription)

            if currency not in monthly_costs:
                monthly_costs[currency] = Decimal('0.0')

            monthly_costs[currency] += monthly_cost

        user_profile.total_monthly_cost = monthly_costs

        return context

    def calculate_monthly_cost(self, subscription):
        """
        Calculate monthly cost based on renewal period.
        """
        from decimal import Decimal

        cost = subscription.cost

        if subscription.renewal_period == 'weekly':
            return cost * Decimal('4.33')  # Average weeks in a month (52/12)
        elif subscription.renewal_period == 'monthly':
            return cost
        elif subscription.renewal_period == 'quarterly':
            return cost / Decimal('3')  # 3 months in a quarter
        elif subscription.renewal_period == 'yearly':
            return cost / Decimal('12')  # 12 months in a year
        elif subscription.renewal_period == 'biennial':
            return cost / Decimal('24')  # 24 months in 2 years
        else:
            return cost  # Default to the cost as is


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating user profile.
    """
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile_update.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        """
        Return the current user.
        """
        return self.request.user

    def form_valid(self, form):
        """
        If the form is valid, save the user and add a success message.
        """
        response = super().form_valid(form)
        messages.success(self.request, "Your profile has been updated successfully.")
        return response


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """
    Admin dashboard view.

    Only accessible to admin users.
    """
    template_name = 'users/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the admin dashboard.
        """
        context = super().get_context_data(**kwargs)

        # Get user statistics
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['admin_users'] = UserProfile.objects.filter(is_admin=True).count()

        # Get subscription statistics
        from subscriptions.models import Subscription
        context['total_subscriptions'] = Subscription.objects.count()
        context['active_subscriptions'] = Subscription.objects.filter(status='active').count()

        # Get recent users
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]

        return context
