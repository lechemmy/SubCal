from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from .models import Subscription, Category, Currency
from django.contrib import messages
from django import forms
import calendar
import io
import requests
import json
from decimal import Decimal
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from django.db.models.functions import Lower
from django.db.models import Sum
from .utils import calculate_next_renewal_date, is_renewal_date, generate_subscriptions_csv, parse_subscriptions_csv, generate_categories_csv, parse_categories_csv, generate_currencies_csv, parse_currencies_csv

# Create your views here.
class SubscriptionListView(ListView):
    model = Subscription
    template_name = 'subscriptions/subscription_list.html'
    context_object_name = 'subscriptions'

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get sort parameters from request
        sort_by = self.request.GET.get('sort', 'name')
        direction = self.request.GET.get('direction', 'asc')

        # Map frontend field names to model field names if needed
        field_mapping = {
            'name': 'name',
            'cost': 'cost',
            'renewal_period': 'renewal_period',
            'start_date': 'start_date',
            'next_billing_date': 'next_billing_date'  # This will be handled specially
        }

        # Apply ordering
        order_field = field_mapping.get(sort_by, 'name')

        # Special handling for next_billing_date since it's not a model field
        if order_field == 'next_billing_date':
            # We'll handle this in get_context_data by sorting the queryset there
            return queryset
        # Use case-insensitive sorting for name field
        elif order_field == 'name':
            if direction == 'desc':
                return queryset.order_by(Lower(order_field).desc())
            else:
                return queryset.order_by(Lower(order_field))
        else:
            if direction == 'desc':
                order_field = f'-{order_field}'
            return queryset.order_by(order_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get current sort parameters to pass to template
        sort_by = self.request.GET.get('sort', 'name')
        direction = self.request.GET.get('direction', 'asc')
        context['current_sort'] = sort_by
        context['current_direction'] = direction

        # Get all subscriptions and calculate next billing date
        subscriptions_list = list(context['subscriptions'])
        from .utils import get_next_billing_date

        for subscription in subscriptions_list:
            subscription.next_billing_date = get_next_billing_date(subscription)

        # Sort by next_billing_date if requested
        if sort_by == 'next_billing_date':
            subscriptions_list.sort(
                key=lambda x: x.next_billing_date,
                reverse=(direction == 'desc')
            )

        # Separate active and cancelled subscriptions
        active_subscriptions = []
        cancelled_subscriptions = []

        for subscription in subscriptions_list:
            if hasattr(subscription, 'status') and subscription.status == 'cancelled':
                cancelled_subscriptions.append(subscription)
            else:
                active_subscriptions.append(subscription)

        # Update the context with the separated lists
        context['active_subscriptions'] = active_subscriptions
        context['cancelled_subscriptions'] = cancelled_subscriptions

        # Keep the original list for backward compatibility
        context['subscriptions'] = subscriptions_list

        # Calculate annual cost for each subscription and group by currency
        annual_totals = {}

        for subscription in subscriptions_list:
            # Skip cancelled subscriptions for annual cost calculation
            if hasattr(subscription, 'status') and subscription.status == 'cancelled':
                continue

            currency = subscription.currency
            annual_cost = subscription.cost

            # Calculate annual cost based on renewal period
            if subscription.renewal_period == 'weekly':
                annual_cost = annual_cost * 52  # 52 weeks in a year
            elif subscription.renewal_period == 'monthly':
                annual_cost = annual_cost * 12  # 12 months in a year
            elif subscription.renewal_period == 'quarterly':
                annual_cost = annual_cost * 4   # 4 quarters in a year
            elif subscription.renewal_period == 'biennial':
                annual_cost = annual_cost / 2   # Cost is every 2 years
            # For yearly, the cost is already annual

            # Add to the appropriate currency total
            if currency not in annual_totals:
                annual_totals[currency] = {
                    'total': 0,
                    'symbol': subscription.get_currency_symbol()
                }

            annual_totals[currency]['total'] += annual_cost

        context['annual_totals'] = annual_totals
        return context

class SubscriptionDetailView(DetailView):
    model = Subscription
    template_name = 'subscriptions/subscription_detail.html'
    context_object_name = 'subscription'

class SubscriptionCreateView(CreateView):
    model = Subscription
    template_name = 'subscriptions/subscription_form.html'
    fields = ['name', 'category', 'cost', 'currency', 'renewal_period', 'start_date', 'url', 'notes']
    success_url = reverse_lazy('subscription-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.all().order_by(Lower('name'))

        # Set default currency if one exists
        default_currency = Currency.objects.filter(is_default=True).first()
        if default_currency:
            form.fields['currency'].initial = default_currency.code

        return form

class SubscriptionUpdateView(UpdateView):
    model = Subscription
    template_name = 'subscriptions/subscription_form.html'
    fields = ['name', 'category', 'cost', 'currency', 'renewal_period', 'start_date', 'status', 'url', 'notes']
    success_url = reverse_lazy('subscription-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.all().order_by(Lower('name'))

        # If the subscription is cancelled, show the cancellation date field
        if self.object and self.object.status == 'cancelled':
            form.fields['cancellation_date'] = forms.DateField(
                required=True,
                widget=forms.DateInput(attrs={'type': 'date'}),
                initial=self.object.cancellation_date
            )

        return form

    def form_valid(self, form):
        response = super().form_valid(form)

        # Handle cancellation date if status is cancelled
        if form.cleaned_data.get('status') == 'cancelled':
            # If cancellation_date is in the form, use it
            if 'cancellation_date' in form.cleaned_data:
                self.object.cancellation_date = form.cleaned_data['cancellation_date']
            # Otherwise, set it to today if it's not already set
            elif not self.object.cancellation_date:
                from django.utils import timezone
                self.object.cancellation_date = timezone.now().date()
            self.object.save()
        # If status is active, clear the cancellation date
        elif form.cleaned_data.get('status') == 'active':
            self.object.cancellation_date = None
            self.object.save()

        return response

class SubscriptionDeleteView(DeleteView):
    model = Subscription
    template_name = 'subscriptions/subscription_confirm_delete.html'
    context_object_name = 'subscription'
    success_url = reverse_lazy('subscription-list')

def home(request):
    # Get all active subscriptions
    subscriptions = Subscription.objects.filter(status='active')

    # Get current date and date 2 weeks from now
    today = datetime.now().date()
    two_weeks_from_now = today + timedelta(days=14)

    # Find subscriptions that are upcoming within the next 2 weeks
    upcoming_subscriptions = []

    for subscription in subscriptions:
        # Check each day in the next 2 weeks
        current_date = today
        while current_date <= two_weeks_from_now:
            if is_renewal_date(subscription, current_date):
                # Add subscription with its renewal date to the list
                upcoming_subscriptions.append({
                    'subscription': subscription,
                    'renewal_date': current_date
                })
                break  # Only add the first renewal date for each subscription
            current_date += timedelta(days=1)

    # Sort upcoming subscriptions by renewal date
    upcoming_subscriptions.sort(key=lambda x: x['renewal_date'])

    context = {
        'upcoming_subscriptions': upcoming_subscriptions
    }

    return render(request, 'subscriptions/home.html', context)

def calendar_view(request):
    # Get current month, year, and view type
    now = datetime.now()
    month = int(request.GET.get('month', now.month))
    year = int(request.GET.get('year', now.year))
    view_type = request.GET.get('view_type', 'month')  # Default to month view

    # Get current day for highlighting in the calendar
    current_day = now.day
    current_month = now.month
    current_year = now.year

    # Get all subscriptions
    # For past dates, include all subscriptions (including cancelled ones for historical view)
    # For future dates, only include active subscriptions
    subscriptions = Subscription.objects.all()

    # Create a wrapper class to hold subscription and is_past flag
    class SubscriptionWrapper:
        def __init__(self, subscription, is_past):
            self.subscription = subscription
            self.is_past = is_past

        def __getattr__(self, name):
            # Delegate attribute access to the wrapped subscription
            return getattr(self.subscription, name)

        def __eq__(self, other):
            # Allow comparison with the wrapped subscription
            if isinstance(other, SubscriptionWrapper):
                return self.subscription == other.subscription
            return self.subscription == other

    if view_type == 'month':
        # Create a calendar for the current month
        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]

        # Calculate renewal dates for each subscription
        calendar_data = {}
        for day_idx, week in enumerate(cal):
            for weekday_idx, day in enumerate(week):
                if day != 0:  # Skip days that are not part of the month
                    calendar_data.setdefault(day, [])

        for subscription in subscriptions:
            start_date = subscription.start_date
            renewal_dates = calculate_next_renewal_date(start_date, subscription.renewal_period, year, month)

            for renewal_date in renewal_dates:
                if renewal_date.day in calendar_data:
                    # Create a wrapper with the subscription and is_past flag
                    is_past = renewal_date < now.date()

                    # Skip cancelled subscriptions for future dates
                    if not is_past and hasattr(subscription, 'status') and subscription.status == 'cancelled':
                        continue

                    subscription_wrapper = SubscriptionWrapper(subscription, is_past)
                    calendar_data[renewal_date.day].append(subscription_wrapper)

        # Previous and next month links
        prev_month = month - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1

        next_month = month + 1
        next_year = year
        if next_month == 13:
            next_month = 1
            next_year += 1

        # Get current year for the year dropdown
        current_year = datetime.now().year

        context = {
            'calendar': cal,
            'month_name': month_name,
            'year': year,
            'month': month,
            'calendar_data': calendar_data,
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'current_year': current_year,
            'current_day': current_day,
            'current_month': current_month,
            'current_year': current_year,
            'view_type': view_type,
        }
    else:  # Year view
        # Create a calendar for each month of the year
        year_calendar = []
        year_calendar_data = {}

        for month_num in range(1, 13):
            month_cal = calendar.monthcalendar(year, month_num)
            month_name = calendar.month_name[month_num]

            # Initialize calendar data for this month
            month_data = {}
            for week in month_cal:
                for day in week:
                    if day != 0:  # Skip days that are not part of the month
                        month_data.setdefault(day, [])

            # Calculate renewal dates for each subscription for this month
            for subscription in subscriptions:
                start_date = subscription.start_date
                renewal_dates = calculate_next_renewal_date(start_date, subscription.renewal_period, year, month_num)

                for renewal_date in renewal_dates:
                    if renewal_date.day in month_data:
                        # Create a wrapper with the subscription and is_past flag
                        is_past = renewal_date < now.date()
                        subscription_wrapper = SubscriptionWrapper(subscription, is_past)
                        month_data[renewal_date.day].append(subscription_wrapper)

            year_calendar.append({
                'month_num': month_num,
                'month_name': month_name,
                'calendar': month_cal,
                'calendar_data': month_data
            })

        # Previous and next year links
        prev_year = year - 1
        next_year = year + 1

        # Get current year for the year dropdown
        current_year = datetime.now().year

        context = {
            'year_calendar': year_calendar,
            'year': year,
            'prev_year': prev_year,
            'next_year': next_year,
            'current_year': current_year,
            'current_day': current_day,
            'current_month': current_month,
            'current_year': current_year,
            'view_type': view_type,
        }

    return render(request, 'subscriptions/subscription_calendar.html', context)

def day_view(request, year, month, day):
    # Create a date object for the selected day
    selected_date = date(year, month, day)
    now = datetime.now().date()
    is_past = selected_date < now

    # Get all subscriptions
    subscriptions = Subscription.objects.all()

    # Calculate subscriptions that renew on this day
    day_subscriptions = []

    for subscription in subscriptions:
        # Skip cancelled subscriptions for future dates
        if not is_past and hasattr(subscription, 'status') and subscription.status == 'cancelled':
            continue

        if is_renewal_date(subscription, selected_date):
            day_subscriptions.append(subscription)

    # Format the date for display
    date_display = selected_date.strftime('%A, %B %d, %Y')

    context = {
        'date': selected_date,
        'date_display': date_display,
        'subscriptions': day_subscriptions,
        'year': year,
        'month': month,
        'day': day,
    }

    return render(request, 'subscriptions/subscription_day.html', context)


class SettingsView(TemplateView):
    template_name = 'subscriptions/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by(Lower('name'))
        context['currencies'] = Currency.objects.all().order_by('code')
        return context


class CategoryListView(ListView):
    model = Category
    template_name = 'subscriptions/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.all().order_by(Lower('name'))


class CategoryCreateView(CreateView):
    model = Category
    template_name = 'subscriptions/category_form.html'
    fields = ['name']
    success_url = reverse_lazy('settings')

    def form_valid(self, form):
        messages.success(self.request, f'Category {form.instance.name} created successfully!')
        return super().form_valid(form)


class CategoryUpdateView(UpdateView):
    model = Category
    template_name = 'subscriptions/category_form.html'
    fields = ['name']
    success_url = reverse_lazy('settings')

    def form_valid(self, form):
        messages.success(self.request, f'Category {form.instance.name} updated successfully!')
        return super().form_valid(form)


class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'subscriptions/category_confirm_delete.html'
    context_object_name = 'category'
    success_url = reverse_lazy('settings')

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        name = category.name
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f'Category {name} deleted successfully!')
        return result


class CurrencyListView(ListView):
    model = Currency
    template_name = 'subscriptions/currency_list.html'
    context_object_name = 'currencies'
    ordering = ['code']


class CurrencyCreateView(CreateView):
    model = Currency
    template_name = 'subscriptions/currency_form.html'
    fields = ['code', 'name', 'symbol', 'is_default']
    success_url = reverse_lazy('settings')

    def form_valid(self, form):
        # If this currency is set as default, unset any other default currencies
        if form.instance.is_default:
            Currency.objects.filter(is_default=True).update(is_default=False)
        messages.success(self.request, f'Currency {form.instance.code} created successfully!')
        return super().form_valid(form)


class CurrencyUpdateView(UpdateView):
    model = Currency
    template_name = 'subscriptions/currency_form.html'
    fields = ['code', 'name', 'symbol', 'is_default']
    success_url = reverse_lazy('settings')

    def form_valid(self, form):
        # If this currency is set as default, unset any other default currencies
        if form.instance.is_default:
            Currency.objects.filter(is_default=True).exclude(pk=form.instance.pk).update(is_default=False)
        messages.success(self.request, f'Currency {form.instance.code} updated successfully!')
        return super().form_valid(form)


class CurrencyDeleteView(DeleteView):
    model = Currency
    template_name = 'subscriptions/currency_confirm_delete.html'
    context_object_name = 'currency'
    success_url = reverse_lazy('settings')

    def delete(self, request, *args, **kwargs):
        currency = self.get_object()
        code = currency.code
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f'Currency {code} deleted successfully!')
        return result


def set_currency_default(request, pk):
    """
    Set a currency as the default currency.
    """
    currency = Currency.objects.get(pk=pk)
    currency.is_default = True
    currency.save()
    messages.success(request, f'Currency {currency.code} set as default successfully!')

    # Redirect back to the referring page, or to settings if no referrer
    referer = request.META.get('HTTP_REFERER')
    if referer and 'currencies' in referer:
        return redirect('currency-list')
    return redirect('settings')


def export_subscriptions_csv(request):
    """
    Export all subscriptions to a CSV file.
    """
    # Get all subscriptions
    subscriptions = Subscription.objects.all().order_by(Lower('name'))

    # Generate CSV data
    csv_data = generate_subscriptions_csv(subscriptions)

    # Create HTTP response with CSV data
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscriptions.csv"'

    return response


def export_categories_csv(request):
    """
    Export all categories to a CSV file.
    """
    # Get all categories
    categories = Category.objects.all().order_by(Lower('name'))

    # Generate CSV data
    csv_data = generate_categories_csv(categories)

    # Create HTTP response with CSV data
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="categories.csv"'

    return response


def export_currencies_csv(request):
    """
    Export all currencies to a CSV file.
    """
    # Get all currencies
    currencies = Currency.objects.all().order_by('code')

    # Generate CSV data
    csv_data = generate_currencies_csv(currencies)

    # Create HTTP response with CSV data
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="currencies.csv"'

    return response


def import_subscriptions_csv(request):
    """
    Import subscriptions from a CSV file.
    """
    if request.method == 'POST':
        # Check if we're processing a form submission from the preview page
        if 'from_preview' in request.POST:
            # Get the data from the session
            subscriptions_data = []
            session_data = request.session.get('import_preview_data', [])

            for sub in session_data:
                # Convert the stored data back to the format expected by the import code
                subscription = {
                    'name': sub.get('name', ''),
                    'category': sub.get('category', ''),
                    'cost': sub.get('cost', ''),
                    'currency': sub.get('currency', ''),
                    'renewal_period': sub.get('renewal_period', ''),
                    'url': sub.get('url', ''),
                    'notes': sub.get('notes', ''),
                    'status': sub.get('status', 'active'),
                    'cancellation_date': sub.get('cancellation_date', None)
                }

                # Convert the date string back to a date object
                if sub.get('start_date'):
                    try:
                        subscription['start_date'] = datetime.fromisoformat(sub['start_date']).date()
                    except ValueError:
                        subscription['start_date'] = datetime.now().date()
                else:
                    subscription['start_date'] = datetime.now().date()

                subscriptions_data.append(subscription)

            # Clear the session data
            if 'import_preview_data' in request.session:
                del request.session['import_preview_data']

            # Process the import
            if 'import_all' in request.POST:
                imported_count = 0
                for subscription_data in subscriptions_data:
                    # Get or create category if provided
                    category = None
                    if subscription_data.get('category'):
                        category, _ = Category.objects.get_or_create(name=subscription_data['category'])

                    # Create subscription
                    Subscription.objects.create(
                        name=subscription_data['name'],
                        category=category,
                        cost=subscription_data['cost'],
                        currency=subscription_data['currency'],
                        renewal_period=subscription_data['renewal_period'],
                        start_date=subscription_data['start_date'],
                        url=subscription_data['url'],
                        notes=subscription_data['notes'],
                        status=subscription_data['status'],
                        cancellation_date=subscription_data['cancellation_date']
                    )
                    imported_count += 1

                messages.success(request, f'Successfully imported {imported_count} subscriptions.')
                return redirect('settings')

            # If 'import_selected' is in POST, import only selected subscriptions
            elif 'import_selected' in request.POST:
                selected_indices = request.POST.getlist('selected_subscriptions')

                if not selected_indices:
                    messages.error(request, 'No subscriptions selected for import.')
                    return redirect('settings')

                imported_count = 0
                for index in selected_indices:
                    try:
                        subscription_data = subscriptions_data[int(index)]

                        # Get or create category if provided
                        category = None
                        if subscription_data.get('category'):
                            category, _ = Category.objects.get_or_create(name=subscription_data['category'])

                        # Create subscription
                        Subscription.objects.create(
                            name=subscription_data['name'],
                            category=category,
                            cost=subscription_data['cost'],
                            currency=subscription_data['currency'],
                            renewal_period=subscription_data['renewal_period'],
                            start_date=subscription_data['start_date'],
                            url=subscription_data['url'],
                            notes=subscription_data['notes'],
                            status=subscription_data['status'],
                            cancellation_date=subscription_data['cancellation_date']
                        )
                        imported_count += 1
                    except (IndexError, ValueError):
                        continue

                messages.success(request, f'Successfully imported {imported_count} subscriptions.')
                return redirect('settings')

        # Handle initial file upload
        else:
            # Check if a file was uploaded
            if 'csv_file' not in request.FILES:
                messages.error(request, 'Please select a CSV file to import.')
                return redirect('settings')

            csv_file = request.FILES['csv_file']

            # Check if it's a CSV file
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return redirect('settings')

            # Parse the CSV file
            try:
                # Decode the file content
                file_data = csv_file.read().decode('utf-8')
                csv_data = io.StringIO(file_data)
                subscriptions_data = parse_subscriptions_csv(csv_data)

                # If no subscriptions were found, show an error
                if not subscriptions_data:
                    messages.error(request, 'No valid subscription data found in the CSV file.')
                    return redirect('settings')

                # Store the parsed data in the session for later use
                request.session['import_preview_data'] = [
                    {
                        'name': sub.get('name', ''),
                        'category': sub.get('category', ''),
                        'cost': str(sub.get('cost', '')),
                        'currency': sub.get('currency', ''),
                        'renewal_period': sub.get('renewal_period', ''),
                        'start_date': sub.get('start_date').isoformat() if sub.get('start_date') else '',
                        'url': sub.get('url', ''),
                        'notes': sub.get('notes', ''),
                        'status': sub.get('status', 'active'),
                        'cancellation_date': sub.get('cancellation_date').isoformat() if sub.get('cancellation_date') else None
                    }
                    for sub in subscriptions_data
                ]

                # Show a preview of the subscriptions to import
                return render(request, 'subscriptions/import_preview.html', {
                    'subscriptions': subscriptions_data
                })

            except Exception as e:
                messages.error(request, f'Error importing CSV file: {str(e)}')
                return redirect('settings')

    # If not a POST request, redirect to settings
    return redirect('settings')


def import_categories_csv(request):
    """
    Import categories from a CSV file.
    """
    if request.method == 'POST':
        # Check if we're processing a form submission from the preview page
        if 'from_preview' in request.POST:
            # Get the data from the session
            categories_data = []
            session_data = request.session.get('import_categories_preview_data', [])

            for cat in session_data:
                # Convert the stored data back to the format expected by the import code
                category = {
                    'name': cat.get('name', '')
                }
                categories_data.append(category)

            # Clear the session data
            if 'import_categories_preview_data' in request.session:
                del request.session['import_categories_preview_data']

            # Process the import
            if 'import_all' in request.POST:
                imported_count = 0
                skipped_count = 0
                for category_data in categories_data:
                    # Skip if category with this name already exists
                    if Category.objects.filter(name=category_data['name']).exists():
                        skipped_count += 1
                        continue

                    # Create category
                    Category.objects.create(
                        name=category_data['name']
                    )
                    imported_count += 1

                if skipped_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} categories. Skipped {skipped_count} duplicate entries.')
                else:
                    messages.success(request, f'Successfully imported {imported_count} categories.')
                return redirect('settings')

            # If 'import_selected' is in POST, import only selected categories
            elif 'import_selected' in request.POST:
                selected_indices = request.POST.getlist('selected_categories')

                if not selected_indices:
                    messages.error(request, 'No categories selected for import.')
                    return redirect('settings')

                imported_count = 0
                skipped_count = 0
                for index in selected_indices:
                    try:
                        category_data = categories_data[int(index)]

                        # Skip if category with this name already exists
                        if Category.objects.filter(name=category_data['name']).exists():
                            skipped_count += 1
                            continue

                        # Create category
                        Category.objects.create(
                            name=category_data['name']
                        )
                        imported_count += 1
                    except (IndexError, ValueError):
                        continue

                if skipped_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} categories. Skipped {skipped_count} duplicate entries.')
                else:
                    messages.success(request, f'Successfully imported {imported_count} categories.')
                return redirect('settings')

        # Handle initial file upload
        else:
            # Check if a file was uploaded
            if 'csv_file' not in request.FILES:
                messages.error(request, 'Please select a CSV file to import.')
                return redirect('settings')

            csv_file = request.FILES['csv_file']

            # Check if it's a CSV file
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return redirect('settings')

            # Parse the CSV file
            try:
                # Decode the file content
                file_data = csv_file.read().decode('utf-8')
                csv_data = io.StringIO(file_data)
                categories_data = parse_categories_csv(csv_data)

                # If no categories were found, show an error
                if not categories_data:
                    messages.error(request, 'No valid category data found in the CSV file.')
                    return redirect('settings')

                # Store the parsed data in the session for later use
                request.session['import_categories_preview_data'] = [
                    {
                        'name': cat.get('name', '')
                    }
                    for cat in categories_data
                ]

                # Show a preview of the categories to import
                return render(request, 'subscriptions/import_categories_preview.html', {
                    'categories': categories_data
                })

            except Exception as e:
                messages.error(request, f'Error importing CSV file: {str(e)}')
                return redirect('settings')

    # If not a POST request, redirect to settings
    return redirect('settings')


def import_currencies_csv(request):
    """
    Import currencies from a CSV file.
    """
    if request.method == 'POST':
        # Check if we're processing a form submission from the preview page
        if 'from_preview' in request.POST:
            # Get the data from the session
            currencies_data = []
            session_data = request.session.get('import_currencies_preview_data', [])

            for curr in session_data:
                # Convert the stored data back to the format expected by the import code
                currency = {
                    'code': curr.get('code', ''),
                    'name': curr.get('name', ''),
                    'symbol': curr.get('symbol', ''),
                    'is_default': curr.get('is_default', False)
                }
                currencies_data.append(currency)

            # Clear the session data
            if 'import_currencies_preview_data' in request.session:
                del request.session['import_currencies_preview_data']

            # Process the import
            if 'import_all' in request.POST:
                imported_count = 0
                skipped_count = 0
                for currency_data in currencies_data:
                    # Skip if currency with this code already exists
                    if Currency.objects.filter(code=currency_data['code']).exists():
                        skipped_count += 1
                        continue

                    # Create currency
                    Currency.objects.create(
                        code=currency_data['code'],
                        name=currency_data['name'],
                        symbol=currency_data['symbol'],
                        is_default=currency_data['is_default']
                    )
                    imported_count += 1

                if skipped_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} currencies. Skipped {skipped_count} duplicate entries.')
                else:
                    messages.success(request, f'Successfully imported {imported_count} currencies.')
                return redirect('settings')

            # If 'import_selected' is in POST, import only selected currencies
            elif 'import_selected' in request.POST:
                selected_indices = request.POST.getlist('selected_currencies')

                if not selected_indices:
                    messages.error(request, 'No currencies selected for import.')
                    return redirect('settings')

                imported_count = 0
                skipped_count = 0
                for index in selected_indices:
                    try:
                        currency_data = currencies_data[int(index)]

                        # Skip if currency with this code already exists
                        if Currency.objects.filter(code=currency_data['code']).exists():
                            skipped_count += 1
                            continue

                        # Create currency
                        Currency.objects.create(
                            code=currency_data['code'],
                            name=currency_data['name'],
                            symbol=currency_data['symbol'],
                            is_default=currency_data['is_default']
                        )
                        imported_count += 1
                    except (IndexError, ValueError):
                        continue

                if skipped_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} currencies. Skipped {skipped_count} duplicate entries.')
                else:
                    messages.success(request, f'Successfully imported {imported_count} currencies.')
                return redirect('settings')

        # Handle initial file upload
        else:
            # Check if a file was uploaded
            if 'csv_file' not in request.FILES:
                messages.error(request, 'Please select a CSV file to import.')
                return redirect('settings')

            csv_file = request.FILES['csv_file']

            # Check if it's a CSV file
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return redirect('settings')

            # Parse the CSV file
            try:
                # Decode the file content
                file_data = csv_file.read().decode('utf-8')
                csv_data = io.StringIO(file_data)
                currencies_data = parse_currencies_csv(csv_data)

                # If no currencies were found, show an error
                if not currencies_data:
                    messages.error(request, 'No valid currency data found in the CSV file.')
                    return redirect('settings')

                # Store the parsed data in the session for later use
                request.session['import_currencies_preview_data'] = [
                    {
                        'code': curr.get('code', ''),
                        'name': curr.get('name', ''),
                        'symbol': curr.get('symbol', ''),
                        'is_default': curr.get('is_default', False)
                    }
                    for curr in currencies_data
                ]

                # Show a preview of the currencies to import
                return render(request, 'subscriptions/import_currencies_preview.html', {
                    'currencies': currencies_data
                })

            except Exception as e:
                messages.error(request, f'Error importing CSV file: {str(e)}')
                return redirect('settings')

    # If not a POST request, redirect to settings
    return redirect('settings')
