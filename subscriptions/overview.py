from django.views.generic import TemplateView
from .models import Subscription, Category, Currency
import requests
import json
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class OverviewView(TemplateView):
    template_name = 'subscriptions/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get year from request or use current year
        selected_year = self.request.GET.get('year')
        current_year = date.today().year

        try:
            selected_year = int(selected_year) if selected_year else current_year
        except ValueError:
            selected_year = current_year

        # Add years for navigation (current year +/- 5 years)
        years = list(range(current_year - 5, current_year + 6))
        context['years'] = years
        context['selected_year'] = selected_year
        context['current_year'] = current_year

        # Get all subscriptions
        subscriptions = Subscription.objects.all()

        # Get exchange rates from API
        exchange_rates = self.get_exchange_rates()

        # Calculate spending by category
        category_spending = self.calculate_category_spending(subscriptions, exchange_rates)
        context['category_spending'] = category_spending

        # Calculate spending by currency
        currency_spending = self.calculate_currency_spending(subscriptions, exchange_rates)
        context['currency_spending'] = currency_spending

        # Calculate spending by subscription
        subscription_spending = self.calculate_subscription_spending(subscriptions, exchange_rates)
        context['subscription_spending'] = subscription_spending

        # Calculate annual cost totals and grand total in GBP
        annual_cost_totals = {}
        grand_total_gbp = Decimal('0.0')

        for subscription in subscriptions:
            currency = subscription.currency
            annual_cost = self.calculate_annual_cost(subscription)

            # Initialize currency if not present
            if currency not in annual_cost_totals:
                annual_cost_totals[currency] = {
                    'original_cost': Decimal('0.0'),
                    'symbol': subscription.get_currency_symbol(),
                    'gbp_cost': Decimal('0.0')
                }

            # Add to totals
            annual_cost_totals[currency]['original_cost'] += annual_cost

            # Convert to GBP and add to GBP total
            gbp_rate = exchange_rates.get(currency, 1.0)
            gbp_cost = annual_cost * Decimal(str(gbp_rate))
            annual_cost_totals[currency]['gbp_cost'] += gbp_cost
            grand_total_gbp += gbp_cost

        context['annual_cost_totals'] = annual_cost_totals
        context['grand_total_gbp'] = grand_total_gbp

        # Calculate monthly billed costs for bar graph (only subscriptions billed in that month)
        monthly_billed_costs = self.calculate_monthly_billed_costs(subscriptions, exchange_rates, selected_year)
        context['monthly_billed_costs'] = monthly_billed_costs

        # Calculate monthly costs for bar graph (all active subscriptions)
        monthly_costs = self.calculate_monthly_costs(subscriptions, exchange_rates, selected_year)
        context['monthly_costs'] = monthly_costs

        # Add exchange rates to context
        context['exchange_rates'] = exchange_rates

        # Add current date and time to context
        context['now'] = datetime.now()

        return context

    def get_exchange_rates(self):
        """Get exchange rates from an online API"""
        try:
            # Using ExchangeRate-API (free tier)
            response = requests.get('https://open.er-api.com/v6/latest/GBP')
            data = response.json()

            if data['result'] == 'success':
                rates = data['rates']
                # Invert rates to get conversion to GBP
                gbp_rates = {}
                for currency, rate in rates.items():
                    gbp_rates[currency] = 1 / rate if rate > 0 else 0

                return gbp_rates
            else:
                # Fallback to hardcoded rates if API fails
                return {
                    'GBP': 1.0,
                    'USD': 0.75,
                    'EUR': 0.85
                }
        except Exception as e:
            # Fallback to hardcoded rates if API fails
            return {
                'GBP': 1.0,
                'USD': 0.75,
                'EUR': 0.85
            }

    def calculate_category_spending(self, subscriptions, exchange_rates):
        """Calculate spending by category with conversion to GBP"""
        # Initialize with all categories from the database
        category_spending = {}
        for category in Category.objects.all():
            category_spending[category.name] = {
                'original_cost': 0,
                'original_currency': 'GBP',  # Default currency
                'gbp_cost': 0
            }

        # Add 'Uncategorized' category
        if 'Uncategorized' not in category_spending:
            category_spending['Uncategorized'] = {
                'original_cost': 0,
                'original_currency': 'GBP',  # Default currency
                'gbp_cost': 0
            }

        # Calculate spending for each subscription
        for subscription in subscriptions:
            category_name = subscription.category.name if subscription.category else 'Uncategorized'

            # Calculate annual cost
            annual_cost = self.calculate_annual_cost(subscription)

            # Convert to GBP
            gbp_rate = exchange_rates.get(subscription.currency, 1.0)
            gbp_cost = annual_cost * Decimal(str(gbp_rate))

            # Update category total
            category_spending[category_name]['original_cost'] += annual_cost
            category_spending[category_name]['original_currency'] = subscription.currency
            category_spending[category_name]['gbp_cost'] += gbp_cost

        return category_spending

    def calculate_currency_spending(self, subscriptions, exchange_rates):
        """Calculate spending by currency with conversion to GBP"""
        currency_spending = {}

        for subscription in subscriptions:
            currency = subscription.currency

            # Calculate annual cost
            annual_cost = self.calculate_annual_cost(subscription)

            # Convert to GBP
            gbp_rate = exchange_rates.get(currency, 1.0)
            gbp_cost = annual_cost * Decimal(str(gbp_rate))

            # Add to currency total
            if currency not in currency_spending:
                currency_spending[currency] = {
                    'original_cost': 0,
                    'gbp_cost': 0,
                    'symbol': subscription.get_currency_symbol()
                }

            currency_spending[currency]['original_cost'] += annual_cost
            currency_spending[currency]['gbp_cost'] += gbp_cost

        return currency_spending

    def calculate_monthly_billed_costs(self, subscriptions, exchange_rates, year=None):
        """Calculate monthly costs for bar graph for a specific year, only including subscriptions billed in that month"""
        # Use current year if not specified
        if year is None:
            year = date.today().year

        # Initialize monthly costs for all 12 months of the specified year
        monthly_billed_costs = {}

        for month in range(1, 13):
            month_date = date(year, month, 1)
            month_key = month_date.strftime('%Y-%m')
            month_name = month_date.strftime('%b %Y')

            monthly_billed_costs[month_key] = {
                'name': month_name,
                'original_costs': {},
                'gbp_cost': 0,
                'date': month_date,  # Store the actual date for comparison
                'subscriptions': []  # Store subscription details for tooltip
            }

        # Calculate costs for each subscription
        for subscription in subscriptions:
            currency = subscription.currency
            cost = subscription.cost
            start_date = subscription.start_date
            name = subscription.name
            renewal_period = subscription.renewal_period

            # Skip if subscription starts after the end of the year
            if start_date.year > year:
                continue

            # Determine billing months based on renewal period and start date
            billing_months = []

            if renewal_period == 'weekly':
                # For weekly, bill every month (approximation)
                billing_months = list(range(1, 13))
            elif renewal_period == 'monthly':
                # For monthly, bill on the same day each month
                billing_months = list(range(1, 13))
            elif renewal_period == 'quarterly':
                # For quarterly, bill every 3 months from start date
                start_month = start_date.month
                for i in range(4):  # 4 quarters in a year
                    month = ((start_month - 1 + i * 3) % 12) + 1
                    if start_date.year < year or (start_date.year == year and start_month <= month):
                        billing_months.append(month)
            elif renewal_period == 'yearly':
                # For yearly, bill once a year on the start month
                if start_date.year < year or start_date.year == year:
                    billing_months.append(start_date.month)
            elif renewal_period == 'biennial':
                # For biennial, bill every 2 years on the start month
                if start_date.year < year and (year - start_date.year) % 2 == 0:
                    billing_months.append(start_date.month)
                elif start_date.year == year:
                    billing_months.append(start_date.month)

            # Calculate full cost (not monthly cost)
            full_cost = subscription.cost

            # Convert to GBP
            gbp_rate = exchange_rates.get(currency, 1.0)
            gbp_full_cost = full_cost * Decimal(str(gbp_rate))

            # Add to monthly costs only for billing months
            for month in billing_months:
                month_date = date(year, month, 1)
                month_key = month_date.strftime('%Y-%m')

                # Skip if month is before subscription start date
                if month_date.replace(day=1) < start_date.replace(day=1):
                    continue

                # Initialize currency if not present
                if currency not in monthly_billed_costs[month_key]['original_costs']:
                    monthly_billed_costs[month_key]['original_costs'][currency] = 0

                # Add costs for this month
                monthly_billed_costs[month_key]['original_costs'][currency] += full_cost
                monthly_billed_costs[month_key]['gbp_cost'] += gbp_full_cost

                # Add subscription details for tooltip
                monthly_billed_costs[month_key]['subscriptions'].append({
                    'name': name,
                    'cost': full_cost,
                    'currency': currency,
                    'symbol': subscription.get_currency_symbol(),
                    'gbp_cost': gbp_full_cost
                })

        # Remove the date field as it's not needed in the template
        for month_data in monthly_billed_costs.values():
            del month_data['date']

        return monthly_billed_costs

    def calculate_monthly_costs(self, subscriptions, exchange_rates, year=None):
        """Calculate monthly costs for bar graph for a specific year, including all active subscriptions"""
        # Use current year if not specified
        if year is None:
            year = date.today().year

        # Initialize monthly costs for all 12 months of the specified year
        monthly_costs = {}

        for month in range(1, 13):
            month_date = date(year, month, 1)
            month_key = month_date.strftime('%Y-%m')
            month_name = month_date.strftime('%b %Y')

            monthly_costs[month_key] = {
                'name': month_name,
                'original_costs': {},
                'gbp_cost': 0,
                'date': month_date,  # Store the actual date for comparison
                'subscriptions': []  # Store subscription details for tooltip
            }

        # Calculate costs for each subscription
        for subscription in subscriptions:
            currency = subscription.currency
            cost = subscription.cost
            start_date = subscription.start_date
            name = subscription.name

            # Calculate monthly cost based on renewal period
            monthly_cost = self.calculate_monthly_cost(subscription)

            # Convert to GBP
            gbp_rate = exchange_rates.get(currency, 1.0)
            gbp_monthly_cost = monthly_cost * Decimal(str(gbp_rate))

            # Add to monthly costs only for months after the subscription start date
            for month_key, month_data in monthly_costs.items():
                # Skip months before the subscription start date
                if month_data['date'].replace(day=1) < start_date.replace(day=1):
                    continue

                # Initialize currency if not present
                if currency not in month_data['original_costs']:
                    month_data['original_costs'][currency] = 0

                # Add costs for this month
                month_data['original_costs'][currency] += monthly_cost
                month_data['gbp_cost'] += gbp_monthly_cost

                # Add subscription details for tooltip
                month_data['subscriptions'].append({
                    'name': name,
                    'cost': monthly_cost,
                    'currency': currency,
                    'symbol': subscription.get_currency_symbol(),
                    'gbp_cost': gbp_monthly_cost
                })

        # Remove the date field as it's not needed in the template
        for month_data in monthly_costs.values():
            del month_data['date']

        return monthly_costs

    def calculate_annual_cost(self, subscription):
        """Calculate annual cost based on renewal period"""
        cost = subscription.cost

        if subscription.renewal_period == 'weekly':
            return cost * 52  # 52 weeks in a year
        elif subscription.renewal_period == 'monthly':
            return cost * 12  # 12 months in a year
        elif subscription.renewal_period == 'quarterly':
            return cost * 4   # 4 quarters in a year
        elif subscription.renewal_period == 'biennial':
            return cost / 2   # Half the cost per year
        else:  # yearly
            return cost

    def calculate_monthly_cost(self, subscription):
        """Calculate monthly cost based on renewal period"""
        cost = subscription.cost

        if subscription.renewal_period == 'weekly':
            return cost * 52 / 12  # 52 weeks / 12 months
        elif subscription.renewal_period == 'monthly':
            return cost
        elif subscription.renewal_period == 'quarterly':
            return cost / 3  # 1 quarter = 3 months
        elif subscription.renewal_period == 'yearly':
            return cost / 12  # 1 year = 12 months
        elif subscription.renewal_period == 'biennial':
            return cost / 24  # 2 years = 24 months
        else:
            return cost  # Default to the cost as is

    def calculate_subscription_spending(self, subscriptions, exchange_rates):
        """Calculate spending by subscription with conversion to GBP"""
        subscription_spending = []

        for subscription in subscriptions:
            # Get subscription details
            name = subscription.name
            category = subscription.category.name if subscription.category else 'Uncategorized'
            currency = subscription.currency
            symbol = subscription.get_currency_symbol()
            renewal_period = subscription.get_renewal_period_display()

            # Calculate annual cost
            annual_cost = self.calculate_annual_cost(subscription)

            # Convert to GBP
            gbp_rate = exchange_rates.get(currency, 1.0)
            gbp_cost = annual_cost * Decimal(str(gbp_rate))

            # Add to subscription spending list
            subscription_spending.append({
                'name': name,
                'category': category,
                'annual_cost': annual_cost,
                'currency': currency,
                'symbol': symbol,
                'renewal_period': renewal_period,
                'gbp_cost': gbp_cost
            })

        # Sort by GBP cost (highest first)
        subscription_spending.sort(key=lambda x: x['gbp_cost'], reverse=True)

        return subscription_spending
