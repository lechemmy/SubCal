from django.db import models
from django.utils import timezone

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=1)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # If this currency is being set as default, unset any other default currencies
        if self.is_default:
            Currency.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} ({self.symbol})"

    class Meta:
        verbose_name_plural = "Currencies"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    ]

    RENEWAL_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('biennial', 'Biennial'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD ($)'),
        ('GBP', 'GBP (£)'),
        ('EUR', 'EUR (€)'),
    ]

    CURRENCY_SYMBOLS = {
        'USD': '$',
        'GBP': '£',
        'EUR': '€',
    }

    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='subscriptions', null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    renewal_period = models.CharField(max_length=10, choices=RENEWAL_CHOICES, default='monthly')
    start_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    cancellation_date = models.DateField(null=True, blank=True)
    url = models.URLField(blank=True, null=True, help_text="Website URL for this subscription")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_currency_symbol(self):
        return self.CURRENCY_SYMBOLS.get(self.currency, '$')

    def cancel(self, cancellation_date=None):
        """
        Cancel the subscription and set the cancellation date.
        If no cancellation date is provided, the current date is used.
        """
        from django.utils import timezone
        self.status = 'cancelled'
        self.cancellation_date = cancellation_date or timezone.now().date()
        self.save()

    def reactivate(self):
        """
        Reactivate a cancelled subscription.
        """
        self.status = 'active'
        self.cancellation_date = None
        self.save()

    def is_cancelled(self):
        """
        Check if the subscription is cancelled.
        """
        return self.status == 'cancelled'

    def __str__(self):
        status_str = f" [CANCELLED]" if self.is_cancelled() else ""
        return f"{self.name}{status_str} ({self.get_currency_symbol()}{self.cost} {self.get_renewal_period_display()})"
