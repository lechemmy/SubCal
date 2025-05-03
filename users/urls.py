"""
URL patterns for the users app.
"""
from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    CustomLoginView, CustomLogoutView, UserRegistrationView,
    CustomPasswordChangeView, CustomPasswordResetView, CustomPasswordResetConfirmView,
    UserProfileView, UserProfileUpdateView, AdminDashboardView
)
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

urlpatterns = [
    # Authentication URLs
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    
    # Password management URLs
    path('password/change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='users/password_change_done.html'
    ), name='password_change_done'),
    
    path('password/reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Profile URLs
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/edit/', UserProfileUpdateView.as_view(), name='profile_edit'),
    
    # Admin URLs
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
]