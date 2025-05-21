from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Subscription

# Register your models here.
@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ('name', 'cost', 'renewal_period', 'start_date', 'created_at', 'updated_at')
    list_filter = ('renewal_period', 'start_date')
    search_fields = ('name', 'notes')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at')
