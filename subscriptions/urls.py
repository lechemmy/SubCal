from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscription-list'),
    path('subscriptions/<int:pk>/', views.SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('subscriptions/new/', views.SubscriptionCreateView.as_view(), name='subscription-create'),
    path('subscriptions/<int:pk>/update/', views.SubscriptionUpdateView.as_view(), name='subscription-update'),
    path('subscriptions/<int:pk>/delete/', views.SubscriptionDeleteView.as_view(), name='subscription-delete'),
    path('subscriptions/calendar/', views.calendar_view, name='subscription-calendar'),
    path('subscriptions/calendar/<int:year>/<int:month>/<int:day>/', views.day_view, name='subscription-day'),

    # Settings and category management
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/new/', views.CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),

    # Currency management
    path('currencies/', views.CurrencyListView.as_view(), name='currency-list'),
    path('currencies/new/', views.CurrencyCreateView.as_view(), name='currency-create'),
    path('currencies/<int:pk>/update/', views.CurrencyUpdateView.as_view(), name='currency-update'),
    path('currencies/<int:pk>/delete/', views.CurrencyDeleteView.as_view(), name='currency-delete'),

    # CSV export/import
    path('subscriptions/export/csv/', views.export_subscriptions_csv, name='export-subscriptions-csv'),
    path('subscriptions/import/csv/', views.import_subscriptions_csv, name='import-subscriptions-csv'),
]
