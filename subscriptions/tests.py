from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.messages import get_messages
from subscriptions.models import Category, Currency, Subscription
from subscriptions import views
from subscriptions.utils import calculate_next_renewal_date, is_renewal_date
from datetime import date, datetime, timedelta
import calendar


# Model Tests
class CategoryModelTest(TestCase):
    """Tests for the Category model."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name="Entertainment")

    def test_category_creation(self):
        """Test that a category can be created."""
        self.assertEqual(self.category.name, "Entertainment")
        self.assertTrue(isinstance(self.category, Category))
        self.assertEqual(str(self.category), "Entertainment")

    def test_category_unique_name(self):
        """Test that category names must be unique."""
        duplicate_category = Category(name="Entertainment")
        with self.assertRaises(Exception):
            duplicate_category.save()

    def test_verbose_name_plural(self):
        """Test the verbose_name_plural is set correctly."""
        self.assertEqual(Category._meta.verbose_name_plural, "Categories")


class CurrencyModelTest(TestCase):
    """Tests for the Currency model."""

    def setUp(self):
        """Set up test data."""
        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$"
        )

    def test_currency_creation(self):
        """Test that a currency can be created."""
        self.assertEqual(self.currency.code, "USD")
        self.assertEqual(self.currency.name, "US Dollar")
        self.assertEqual(self.currency.symbol, "$")
        self.assertTrue(isinstance(self.currency, Currency))
        self.assertEqual(str(self.currency), "USD ($)")

    def test_currency_unique_code(self):
        """Test that currency codes must be unique."""
        duplicate_currency = Currency(code="USD", name="US Dollar", symbol="$")
        with self.assertRaises(Exception):
            duplicate_currency.save()

    def test_verbose_name_plural(self):
        """Test the verbose_name_plural is set correctly."""
        self.assertEqual(Currency._meta.verbose_name_plural, "Currencies")


class SubscriptionModelTest(TestCase):
    """Tests for the Subscription model."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name="Entertainment")
        self.subscription = Subscription.objects.create(
            name="Netflix",
            category=self.category,
            cost=9.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 1)
        )

    def test_subscription_creation(self):
        """Test that a subscription can be created."""
        self.assertEqual(self.subscription.name, "Netflix")
        self.assertEqual(self.subscription.category, self.category)
        self.assertEqual(float(self.subscription.cost), 9.99)
        self.assertEqual(self.subscription.currency, "USD")
        self.assertEqual(self.subscription.renewal_period, "monthly")
        self.assertEqual(self.subscription.start_date, date(2023, 1, 1))
        self.assertTrue(isinstance(self.subscription, Subscription))

    def test_get_currency_symbol(self):
        """Test the get_currency_symbol method."""
        self.assertEqual(self.subscription.get_currency_symbol(), "$")

        # Test with different currencies
        self.subscription.currency = "EUR"
        self.assertEqual(self.subscription.get_currency_symbol(), "€")

        self.subscription.currency = "GBP"
        self.assertEqual(self.subscription.get_currency_symbol(), "£")

        # Test with unknown currency (should default to $)
        self.subscription.currency = "XYZ"
        self.assertEqual(self.subscription.get_currency_symbol(), "$")

    def test_string_representation(self):
        """Test the string representation of a subscription."""
        expected_string = "Netflix ($9.99 Monthly)"
        self.assertEqual(str(self.subscription), expected_string)

    def test_subscription_with_null_category(self):
        """Test that a subscription can be created without a category."""
        subscription = Subscription.objects.create(
            name="Amazon Prime",
            cost=12.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 1)
        )
        self.assertIsNone(subscription.category)
        self.assertEqual(subscription.name, "Amazon Prime")

    def test_subscription_with_notes(self):
        """Test that a subscription can have notes."""
        subscription = Subscription.objects.create(
            name="Disney+",
            cost=7.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 1),
            notes="Family subscription"
        )
        self.assertEqual(subscription.notes, "Family subscription")

    def test_subscription_renewal_choices(self):
        """Test the renewal period choices."""
        # Test valid choices
        for choice in ['weekly', 'monthly', 'yearly']:
            subscription = Subscription(
                name=f"Test {choice}",
                cost=9.99,
                currency="USD",
                renewal_period=choice,
                start_date=date(2023, 1, 1)
            )
            # Only validate the renewal_period field
            subscription.clean_fields(exclude=['cost'])

        # Test invalid choice
        subscription = Subscription(
            name="Test invalid",
            cost=9.99,
            currency="USD",
            renewal_period="invalid",
            start_date=date(2023, 1, 1)
        )
        with self.assertRaises(ValidationError):
            # Only validate the renewal_period field
            subscription.clean_fields(exclude=['cost'])

    def test_subscription_currency_choices(self):
        """Test the currency choices."""
        # Test valid choices
        for choice in ['USD', 'GBP', 'EUR']:
            subscription = Subscription(
                name=f"Test {choice}",
                cost=9.99,
                currency=choice,
                renewal_period="monthly",
                start_date=date(2023, 1, 1)
            )
            # Only validate the currency field
            subscription.clean_fields(exclude=['cost'])

        # Test invalid choice
        subscription = Subscription(
            name="Test invalid",
            cost=9.99,
            currency="invalid",
            renewal_period="monthly",
            start_date=date(2023, 1, 1)
        )
        with self.assertRaises(ValidationError):
            # Only validate the currency field
            subscription.clean_fields(exclude=['cost'])


# View Tests
class HomeViewTest(TestCase):
    """Tests for the home view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('home')

    def test_home_view_status_code(self):
        """Test that the home view returns a 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_home_view_template(self):
        """Test that the home view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'subscriptions/home.html')


class SubscriptionListViewTest(TestCase):
    """Tests for the subscription list view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('subscription-list')
        self.category = Category.objects.create(name="Entertainment")
        self.subscription1 = Subscription.objects.create(
            name="Netflix",
            category=self.category,
            cost=9.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 1)
        )
        self.subscription2 = Subscription.objects.create(
            name="Amazon Prime",
            cost=12.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 1)
        )

    def test_subscription_list_view_status_code(self):
        """Test that the subscription list view returns a 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_subscription_list_view_template(self):
        """Test that the subscription list view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'subscriptions/subscription_list.html')

    def test_subscription_list_view_context(self):
        """Test that the subscription list view contains the correct context."""
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['subscriptions']), 2)
        self.assertIn(self.subscription1, response.context['subscriptions'])
        self.assertIn(self.subscription2, response.context['subscriptions'])


class SubscriptionDetailViewTest(TestCase):
    """Tests for the subscription detail view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.category = Category.objects.create(name="Entertainment")
        self.subscription = Subscription.objects.create(
            name="Netflix",
            category=self.category,
            cost=9.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 1)
        )
        self.url = reverse('subscription-detail', args=[self.subscription.pk])

    def test_subscription_detail_view_status_code(self):
        """Test that the subscription detail view returns a 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_subscription_detail_view_template(self):
        """Test that the subscription detail view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'subscriptions/subscription_detail.html')

    def test_subscription_detail_view_context(self):
        """Test that the subscription detail view contains the correct context."""
        response = self.client.get(self.url)
        self.assertEqual(response.context['subscription'], self.subscription)

    def test_subscription_detail_view_404(self):
        """Test that the subscription detail view returns a 404 for non-existent subscriptions."""
        url = reverse('subscription-detail', args=[999])  # Non-existent ID
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class SubscriptionCreateViewTest(TestCase):
    """Tests for the subscription create view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('subscription-create')
        self.category = Category.objects.create(name="Entertainment")

    def test_subscription_create_view_status_code(self):
        """Test that the subscription create view returns a 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_subscription_create_view_template(self):
        """Test that the subscription create view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'subscriptions/subscription_form.html')

    def test_subscription_create_view_form_submission(self):
        """Test that the subscription create view can create a subscription."""
        data = {
            'name': 'Disney+',
            'category': self.category.pk,
            'cost': 7.99,
            'currency': 'USD',
            'renewal_period': 'monthly',
            'start_date': '2023-01-01',
            'notes': 'Family subscription'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Subscription.objects.count(), 1)
        subscription = Subscription.objects.first()
        self.assertEqual(subscription.name, 'Disney+')
        self.assertEqual(subscription.category, self.category)
        self.assertEqual(float(subscription.cost), 7.99)
        self.assertEqual(subscription.notes, 'Family subscription')


class SubscriptionUpdateViewTest(TestCase):
    """Tests for the subscription update view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.category = Category.objects.create(name="Entertainment")
        self.subscription = Subscription.objects.create(
            name="Netflix",
            category=self.category,
            cost=9.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 1)
        )
        self.url = reverse('subscription-update', args=[self.subscription.pk])

    def test_subscription_update_view_status_code(self):
        """Test that the subscription update view returns a 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_subscription_update_view_template(self):
        """Test that the subscription update view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'subscriptions/subscription_form.html')

    def test_subscription_update_view_form_submission(self):
        """Test that the subscription update view can update a subscription."""
        data = {
            'name': 'Netflix Premium',
            'category': self.category.pk,
            'cost': 14.99,
            'currency': 'USD',
            'renewal_period': 'monthly',
            'start_date': '2023-01-01',
            'notes': 'Premium subscription'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.name, 'Netflix Premium')
        self.assertEqual(float(self.subscription.cost), 14.99)
        self.assertEqual(self.subscription.notes, 'Premium subscription')


class SubscriptionDeleteViewTest(TestCase):
    """Tests for the subscription delete view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.category = Category.objects.create(name="Entertainment")
        self.subscription = Subscription.objects.create(
            name="Netflix",
            category=self.category,
            cost=9.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 1)
        )
        self.url = reverse('subscription-delete', args=[self.subscription.pk])

    def test_subscription_delete_view_status_code(self):
        """Test that the subscription delete view returns a 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_subscription_delete_view_template(self):
        """Test that the subscription delete view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'subscriptions/subscription_confirm_delete.html')

    def test_subscription_delete_view_deletion(self):
        """Test that the subscription delete view can delete a subscription."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        self.assertEqual(Subscription.objects.count(), 0)


class CalendarViewTest(TestCase):
    """Tests for the calendar view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('subscription-calendar')
        self.category = Category.objects.create(name="Entertainment")
        self.subscription = Subscription.objects.create(
            name="Netflix",
            category=self.category,
            cost=9.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 1)
        )

    def test_calendar_view_status_code(self):
        """Test that the calendar view returns a 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_calendar_view_template(self):
        """Test that the calendar view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'subscriptions/subscription_calendar.html')

    def test_calendar_view_context(self):
        """Test that the calendar view contains the correct context."""
        now = datetime.now()
        response = self.client.get(self.url)
        self.assertIn('calendar', response.context)
        self.assertIn('month_name', response.context)
        self.assertIn('year', response.context)
        self.assertIn('month', response.context)
        self.assertIn('calendar_data', response.context)
        self.assertIn('prev_month', response.context)
        self.assertIn('prev_year', response.context)
        self.assertIn('next_month', response.context)
        self.assertIn('next_year', response.context)
        self.assertIn('current_year', response.context)

        # Test with specific month and year
        url = f"{self.url}?month=1&year=2023"
        response = self.client.get(url)
        self.assertEqual(response.context['month'], 1)
        self.assertEqual(response.context['year'], 2023)
        self.assertEqual(response.context['month_name'], 'January')

        # Check if our subscription is in the calendar data for day 1
        self.assertIn(1, response.context['calendar_data'])
        self.assertIn(self.subscription, response.context['calendar_data'][1])


class DayViewTest(TestCase):
    """Tests for the day view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.category = Category.objects.create(name="Entertainment")
        self.subscription = Subscription.objects.create(
            name="Netflix",
            category=self.category,
            cost=9.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 1)
        )
        self.url = reverse('subscription-day', args=[2023, 1, 1])

    def test_day_view_status_code(self):
        """Test that the day view returns a 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_day_view_template(self):
        """Test that the day view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'subscriptions/subscription_day.html')

    def test_day_view_context(self):
        """Test that the day view contains the correct context."""
        response = self.client.get(self.url)
        self.assertIn('date', response.context)
        self.assertIn('date_display', response.context)
        self.assertIn('subscriptions', response.context)
        self.assertIn('year', response.context)
        self.assertIn('month', response.context)
        self.assertIn('day', response.context)

        # Check if our subscription is in the context
        self.assertIn(self.subscription, response.context['subscriptions'])

        # Test a day without subscriptions
        url = reverse('subscription-day', args=[2023, 1, 2])
        response = self.client.get(url)
        self.assertEqual(len(response.context['subscriptions']), 0)


class SettingsViewTest(TestCase):
    """Tests for the settings view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('settings')
        self.category = Category.objects.create(name="Entertainment")
        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$"
        )

    def test_settings_view_status_code(self):
        """Test that the settings view returns a 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_settings_view_template(self):
        """Test that the settings view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'subscriptions/settings.html')

    def test_settings_view_context(self):
        """Test that the settings view contains the correct context."""
        response = self.client.get(self.url)
        self.assertIn('categories', response.context)
        self.assertIn('currencies', response.context)
        self.assertIn(self.category, response.context['categories'])
        self.assertIn(self.currency, response.context['currencies'])


# Category and Currency View Tests
class CategoryViewsTest(TestCase):
    """Tests for the Category views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.category = Category.objects.create(name="Entertainment")
        self.list_url = reverse('category-list')
        self.create_url = reverse('category-create')
        self.update_url = reverse('category-update', args=[self.category.pk])
        self.delete_url = reverse('category-delete', args=[self.category.pk])

    def test_category_list_view(self):
        """Test the category list view."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/category_list.html')
        self.assertIn(self.category, response.context['categories'])

    def test_category_create_view_get(self):
        """Test the GET request to the category create view."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/category_form.html')

    def test_category_create_view_post(self):
        """Test the POST request to the category create view."""
        data = {'name': 'Technology'}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Category.objects.count(), 2)
        self.assertTrue(Category.objects.filter(name='Technology').exists())

        # Test for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Technology created successfully', str(messages[0]))

    def test_category_update_view_get(self):
        """Test the GET request to the category update view."""
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/category_form.html')

    def test_category_update_view_post(self):
        """Test the POST request to the category update view."""
        data = {'name': 'Entertainment & Media'}
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Entertainment & Media')

        # Test for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Entertainment & Media updated successfully', str(messages[0]))

    def test_category_delete_view_get(self):
        """Test the GET request to the category delete view."""
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/category_confirm_delete.html')

    def test_category_delete_view_post(self):
        """Test the POST request to the category delete view."""
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        self.assertEqual(Category.objects.count(), 0)

        # Test for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Entertainment deleted successfully', str(messages[0]))


class CurrencyViewsTest(TestCase):
    """Tests for the Currency views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$"
        )
        self.list_url = reverse('currency-list')
        self.create_url = reverse('currency-create')
        self.update_url = reverse('currency-update', args=[self.currency.pk])
        self.delete_url = reverse('currency-delete', args=[self.currency.pk])

    def test_currency_list_view(self):
        """Test the currency list view."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/currency_list.html')
        self.assertIn(self.currency, response.context['currencies'])

    def test_currency_create_view_get(self):
        """Test the GET request to the currency create view."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/currency_form.html')

    def test_currency_create_view_post(self):
        """Test the POST request to the currency create view."""
        data = {
            'code': 'EUR',
            'name': 'Euro',
            'symbol': '€'
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Currency.objects.count(), 2)
        self.assertTrue(Currency.objects.filter(code='EUR').exists())

        # Test for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('EUR created successfully', str(messages[0]))

    def test_currency_update_view_get(self):
        """Test the GET request to the currency update view."""
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/currency_form.html')

    def test_currency_update_view_post(self):
        """Test the POST request to the currency update view."""
        data = {
            'code': 'USD',
            'name': 'United States Dollar',
            'symbol': '$'
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.currency.refresh_from_db()
        self.assertEqual(self.currency.name, 'United States Dollar')

        # Test for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('USD updated successfully', str(messages[0]))

    def test_currency_delete_view_get(self):
        """Test the GET request to the currency delete view."""
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/currency_confirm_delete.html')

    def test_currency_delete_view_post(self):
        """Test the POST request to the currency delete view."""
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        self.assertEqual(Currency.objects.count(), 0)

        # Test for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('USD deleted successfully', str(messages[0]))


# Utils Tests
class UtilsTest(TestCase):
    """Tests for the utility functions."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name="Entertainment")
        self.subscription_monthly = Subscription.objects.create(
            name="Monthly on 30th",
            category=self.category,
            cost=9.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2023, 1, 30)  # January 30th
        )
        self.subscription_quarterly = Subscription.objects.create(
            name="Quarterly on 31st",
            category=self.category,
            cost=29.99,
            currency="USD",
            renewal_period="quarterly",
            start_date=date(2023, 1, 31)  # January 31st
        )
        self.subscription_yearly = Subscription.objects.create(
            name="Yearly on 29th",
            category=self.category,
            cost=99.99,
            currency="USD",
            renewal_period="yearly",
            start_date=date(2023, 1, 29)  # January 29th
        )

    def test_calculate_next_renewal_date_monthly(self):
        """Test calculate_next_renewal_date for monthly subscriptions."""
        # January 30th subscription in February (28 days in non-leap year)
        # Should move to February 28th (the last day of the month)
        renewal_dates = calculate_next_renewal_date(
            self.subscription_monthly.start_date,
            self.subscription_monthly.renewal_period,
            2023,  # Non-leap year
            2      # February
        )
        self.assertEqual(len(renewal_dates), 1)
        self.assertEqual(renewal_dates[0], date(2023, 2, 28))

        # January 30th subscription in March (31 days)
        # Should stay on 30th
        renewal_dates = calculate_next_renewal_date(
            self.subscription_monthly.start_date,
            self.subscription_monthly.renewal_period,
            2023,
            3      # March
        )
        self.assertEqual(len(renewal_dates), 1)
        self.assertEqual(renewal_dates[0], date(2023, 3, 30))

        # January 30th subscription in April (30 days)
        # Should stay on 30th
        renewal_dates = calculate_next_renewal_date(
            self.subscription_monthly.start_date,
            self.subscription_monthly.renewal_period,
            2023,
            4      # April
        )
        self.assertEqual(len(renewal_dates), 1)
        self.assertEqual(renewal_dates[0], date(2023, 4, 30))

    def test_calculate_next_renewal_date_quarterly(self):
        """Test calculate_next_renewal_date for quarterly subscriptions."""
        # January 31st subscription in April (30 days)
        # Should move to April 30th (the last day of the month)
        renewal_dates = calculate_next_renewal_date(
            self.subscription_quarterly.start_date,
            self.subscription_quarterly.renewal_period,
            2023,
            4      # April
        )
        self.assertEqual(len(renewal_dates), 1)
        self.assertEqual(renewal_dates[0], date(2023, 4, 30))

        # January 31st subscription in July (31 days)
        # Should stay on 31st
        renewal_dates = calculate_next_renewal_date(
            self.subscription_quarterly.start_date,
            self.subscription_quarterly.renewal_period,
            2023,
            7      # July
        )
        self.assertEqual(len(renewal_dates), 1)
        self.assertEqual(renewal_dates[0], date(2023, 7, 31))

    def test_calculate_next_renewal_date_yearly(self):
        """Test calculate_next_renewal_date for yearly subscriptions."""
        # January 29th subscription in January of a non-leap year
        # Should stay on 29th
        renewal_dates = calculate_next_renewal_date(
            self.subscription_yearly.start_date,
            self.subscription_yearly.renewal_period,
            2023,  # Non-leap year
            1      # January
        )
        self.assertEqual(len(renewal_dates), 1)
        self.assertEqual(renewal_dates[0], date(2023, 1, 29))

        # January 29th subscription in January of a leap year
        # Should stay on 29th
        renewal_dates = calculate_next_renewal_date(
            self.subscription_yearly.start_date,
            self.subscription_yearly.renewal_period,
            2024,  # Leap year
            1      # January
        )
        self.assertEqual(len(renewal_dates), 1)
        self.assertEqual(renewal_dates[0], date(2024, 1, 29))

    def test_is_renewal_date(self):
        """Test is_renewal_date function."""
        # Monthly subscription on 30th
        # February 28th, 2023 is a renewal date (February doesn't have 30th, so use the last day)
        self.assertTrue(is_renewal_date(
            self.subscription_monthly,
            date(2023, 2, 28)
        ))

        # February 1st, 2023 is not a renewal date
        self.assertFalse(is_renewal_date(
            self.subscription_monthly,
            date(2023, 2, 1)
        ))

        # March 30th, 2023 is a renewal date
        self.assertTrue(is_renewal_date(
            self.subscription_monthly,
            date(2023, 3, 30)
        ))

        # Quarterly subscription on 31st
        # April 30th, 2023 is a renewal date (April doesn't have 31st, so use the last day)
        self.assertTrue(is_renewal_date(
            self.subscription_quarterly,
            date(2023, 4, 30)
        ))

        # April 1st, 2023 is not a renewal date
        self.assertFalse(is_renewal_date(
            self.subscription_quarterly,
            date(2023, 4, 1)
        ))

        # July 31st, 2023 is a renewal date
        self.assertTrue(is_renewal_date(
            self.subscription_quarterly,
            date(2023, 7, 31)
        ))

    def test_leap_year_edge_case(self):
        """Test leap year edge case."""
        # Create a subscription that starts on February 29th of a leap year
        leap_year_subscription = Subscription.objects.create(
            name="Leap Year Subscription",
            category=self.category,
            cost=19.99,
            currency="USD",
            renewal_period="monthly",
            start_date=date(2020, 2, 29)  # February 29th, 2020 (leap year)
        )

        # March 29th, 2020 is a renewal date
        self.assertTrue(is_renewal_date(
            leap_year_subscription,
            date(2020, 3, 29)
        ))

        # February 28th, 2021 is a renewal date (February 2021 doesn't have 29th, so use the last day)
        self.assertTrue(is_renewal_date(
            leap_year_subscription,
            date(2021, 2, 28)
        ))

        # February 1st, 2021 is not a renewal date
        self.assertFalse(is_renewal_date(
            leap_year_subscription,
            date(2021, 2, 1)
        ))

        # February 29th, 2024 is a renewal date (leap year)
        self.assertTrue(is_renewal_date(
            leap_year_subscription,
            date(2024, 2, 29)
        ))


# URL Tests
class UrlsTest(TestCase):
    """Tests for URL routing."""

    def test_home_url(self):
        """Test the home URL."""
        url = reverse('home')
        self.assertEqual(url, '/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.home)

    def test_subscription_list_url(self):
        """Test the subscription list URL."""
        url = reverse('subscription-list')
        self.assertEqual(url, '/subscriptions/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.SubscriptionListView)

    def test_subscription_detail_url(self):
        """Test the subscription detail URL."""
        url = reverse('subscription-detail', args=[1])
        self.assertEqual(url, '/subscriptions/1/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.SubscriptionDetailView)

    def test_subscription_create_url(self):
        """Test the subscription create URL."""
        url = reverse('subscription-create')
        self.assertEqual(url, '/subscriptions/new/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.SubscriptionCreateView)

    def test_subscription_update_url(self):
        """Test the subscription update URL."""
        url = reverse('subscription-update', args=[1])
        self.assertEqual(url, '/subscriptions/1/update/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.SubscriptionUpdateView)

    def test_subscription_delete_url(self):
        """Test the subscription delete URL."""
        url = reverse('subscription-delete', args=[1])
        self.assertEqual(url, '/subscriptions/1/delete/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.SubscriptionDeleteView)

    def test_subscription_calendar_url(self):
        """Test the subscription calendar URL."""
        url = reverse('subscription-calendar')
        self.assertEqual(url, '/subscriptions/calendar/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.calendar_view)

    def test_subscription_day_url(self):
        """Test the subscription day URL."""
        url = reverse('subscription-day', args=[2023, 1, 1])
        self.assertEqual(url, '/subscriptions/calendar/2023/1/1/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.day_view)

    def test_settings_url(self):
        """Test the settings URL."""
        url = reverse('settings')
        self.assertEqual(url, '/settings/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.SettingsView)

    def test_category_list_url(self):
        """Test the category list URL."""
        url = reverse('category-list')
        self.assertEqual(url, '/categories/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CategoryListView)

    def test_category_create_url(self):
        """Test the category create URL."""
        url = reverse('category-create')
        self.assertEqual(url, '/categories/new/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CategoryCreateView)

    def test_category_update_url(self):
        """Test the category update URL."""
        url = reverse('category-update', args=[1])
        self.assertEqual(url, '/categories/1/update/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CategoryUpdateView)

    def test_category_delete_url(self):
        """Test the category delete URL."""
        url = reverse('category-delete', args=[1])
        self.assertEqual(url, '/categories/1/delete/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CategoryDeleteView)

    def test_currency_list_url(self):
        """Test the currency list URL."""
        url = reverse('currency-list')
        self.assertEqual(url, '/currencies/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CurrencyListView)

    def test_currency_create_url(self):
        """Test the currency create URL."""
        url = reverse('currency-create')
        self.assertEqual(url, '/currencies/new/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CurrencyCreateView)

    def test_currency_update_url(self):
        """Test the currency update URL."""
        url = reverse('currency-update', args=[1])
        self.assertEqual(url, '/currencies/1/update/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CurrencyUpdateView)

    def test_currency_delete_url(self):
        """Test the currency delete URL."""
        url = reverse('currency-delete', args=[1])
        self.assertEqual(url, '/currencies/1/delete/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, views.CurrencyDeleteView)
