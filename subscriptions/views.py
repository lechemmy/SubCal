from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from .models import Subscription, Category, Currency
from django.contrib import messages
import calendar
import io
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from .utils import calculate_next_renewal_date, is_renewal_date, generate_subscriptions_csv, parse_subscriptions_csv

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
            'start_date': 'start_date'
        }

        # Apply ordering
        order_field = field_mapping.get(sort_by, 'name')
        if direction == 'desc':
            order_field = f'-{order_field}'

        return queryset.order_by(order_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get current sort parameters to pass to template
        context['current_sort'] = self.request.GET.get('sort', 'name')
        context['current_direction'] = self.request.GET.get('direction', 'asc')

        # Calculate annual cost for each subscription and group by currency
        annual_totals = {}

        for subscription in context['subscriptions']:
            currency = subscription.currency
            annual_cost = subscription.cost

            # Calculate annual cost based on renewal period
            if subscription.renewal_period == 'weekly':
                annual_cost = annual_cost * 52  # 52 weeks in a year
            elif subscription.renewal_period == 'monthly':
                annual_cost = annual_cost * 12  # 12 months in a year
            elif subscription.renewal_period == 'quarterly':
                annual_cost = annual_cost * 4   # 4 quarters in a year
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
    fields = ['name', 'category', 'cost', 'currency', 'renewal_period', 'start_date', 'notes']
    success_url = reverse_lazy('subscription-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.all().order_by('name')

        # Set default currency if one exists
        default_currency = Currency.objects.filter(is_default=True).first()
        if default_currency:
            form.fields['currency'].initial = default_currency.code

        return form

class SubscriptionUpdateView(UpdateView):
    model = Subscription
    template_name = 'subscriptions/subscription_form.html'
    fields = ['name', 'category', 'cost', 'currency', 'renewal_period', 'start_date', 'notes']
    success_url = reverse_lazy('subscription-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.all().order_by('name')
        return form

class SubscriptionDeleteView(DeleteView):
    model = Subscription
    template_name = 'subscriptions/subscription_confirm_delete.html'
    context_object_name = 'subscription'
    success_url = reverse_lazy('subscription-list')

def home(request):
    return render(request, 'subscriptions/home.html')

def calendar_view(request):
    # Get current month, year, and view type
    now = datetime.now()
    month = int(request.GET.get('month', now.month))
    year = int(request.GET.get('year', now.year))
    view_type = request.GET.get('view_type', 'month')  # Default to month view

    # Get all subscriptions
    subscriptions = Subscription.objects.all()

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
                    calendar_data[renewal_date.day].append(subscription)

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
                        month_data[renewal_date.day].append(subscription)

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
            'view_type': view_type,
        }

    return render(request, 'subscriptions/subscription_calendar.html', context)

def day_view(request, year, month, day):
    # Create a date object for the selected day
    selected_date = date(year, month, day)

    # Get all subscriptions
    subscriptions = Subscription.objects.all()

    # Calculate subscriptions that renew on this day
    day_subscriptions = []

    for subscription in subscriptions:
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
        context['categories'] = Category.objects.all().order_by('name')
        context['currencies'] = Currency.objects.all().order_by('code')
        return context


class CategoryListView(ListView):
    model = Category
    template_name = 'subscriptions/category_list.html'
    context_object_name = 'categories'
    ordering = ['name']


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
    subscriptions = Subscription.objects.all().order_by('name')

    # Generate CSV data
    csv_data = generate_subscriptions_csv(subscriptions)

    # Create HTTP response with CSV data
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscriptions.csv"'

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
                    'notes': sub.get('notes', '')
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
                        notes=subscription_data['notes']
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
                            notes=subscription_data['notes']
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
                        'notes': sub.get('notes', '')
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
