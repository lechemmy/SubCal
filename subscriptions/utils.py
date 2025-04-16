from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import csv
import io

def calculate_next_renewal_date(start_date, renewal_period, target_year, target_month):
    """
    Calculate the next renewal date for a subscription.

    If the renewal day doesn't exist in the target month (e.g., February 30th),
    move it to the last valid date of the month for that occurrence only.
    For example, a 30th Jan monthly subscription will fall next on 28th February, then 30th March.

    Args:
        start_date: The start date of the subscription
        renewal_period: The renewal period ('weekly', 'monthly', 'quarterly', 'yearly')
        target_year: The year to calculate the renewal date for
        target_month: The month to calculate the renewal date for

    Returns:
        A list of datetime.date objects representing the renewal dates in the target month
    """
    renewal_dates = []

    if renewal_period == 'weekly':
        # For weekly, calculate all renewal dates in the month
        current_date = start_date
        while current_date.year < target_year or (current_date.year == target_year and current_date.month < target_month):
            current_date += timedelta(days=7)

        while current_date.year == target_year and current_date.month == target_month:
            renewal_dates.append(current_date)
            current_date += timedelta(days=7)

    elif renewal_period == 'monthly':
        # For monthly, check if the start day is in this month
        day = start_date.day
        # Get the last day of the target month
        last_day = calendar.monthrange(target_year, target_month)[1]

        # If the start day is greater than the last day of the target month,
        # use the last day of the target month
        if day > last_day:
            renewal_date = datetime(target_year, target_month, last_day).date()
        else:
            renewal_date = datetime(target_year, target_month, day).date()

        # Only add the renewal date if it's after the start date
        if renewal_date >= start_date:
            renewal_dates.append(renewal_date)

    elif renewal_period == 'quarterly':
        # For quarterly, check if this month is a quarterly renewal month
        months_since_start = (target_year - start_date.year) * 12 + target_month - start_date.month
        if months_since_start % 3 == 0:
            day = start_date.day
            # Get the last day of the target month
            last_day = calendar.monthrange(target_year, target_month)[1]

            # If the start day is greater than the last day of the target month,
            # use the last day of the target month
            if day > last_day:
                renewal_date = datetime(target_year, target_month, last_day).date()
            else:
                renewal_date = datetime(target_year, target_month, day).date()

            # Only add the renewal date if it's after the start date
            if renewal_date >= start_date:
                renewal_dates.append(renewal_date)

    elif renewal_period == 'yearly':
        # For yearly, check if the start month is this month
        if start_date.month == target_month:
            day = start_date.day
            # Get the last day of the target month
            last_day = calendar.monthrange(target_year, target_month)[1]

            # If the start day is greater than the last day of the target month,
            # use the last day of the target month
            if day > last_day:
                renewal_date = datetime(target_year, target_month, last_day).date()
            else:
                renewal_date = datetime(target_year, target_month, day).date()

            # Only add the renewal date if it's after the start date
            if renewal_date >= start_date:
                renewal_dates.append(renewal_date)

    elif renewal_period == 'biennial':
        # For biennial, check if the start month is this month and if this is a biennial year
        years_since_start = target_year - start_date.year
        if start_date.month == target_month and years_since_start % 2 == 0:
            day = start_date.day
            # Get the last day of the target month
            last_day = calendar.monthrange(target_year, target_month)[1]

            # If the start day is greater than the last day of the target month,
            # use the last day of the target month
            if day > last_day:
                renewal_date = datetime(target_year, target_month, last_day).date()
            else:
                renewal_date = datetime(target_year, target_month, day).date()

            # Only add the renewal date if it's after the start date
            if renewal_date >= start_date:
                renewal_dates.append(renewal_date)

    return renewal_dates

def is_renewal_date(subscription, check_date):
    """
    Check if a subscription renews on a specific date.

    If the subscription's renewal day doesn't exist in the month,
    it renews on the last valid date of the month for that occurrence only.
    For example, a 30th Jan monthly subscription will fall next on 28th February, then 30th March.

    If the subscription is cancelled and the check_date is after the cancellation date,
    this function will return False.

    Args:
        subscription: The subscription to check
        check_date: The date to check

    Returns:
        True if the subscription renews on the check_date, False otherwise
    """
    start_date = subscription.start_date
    renewal_period = subscription.renewal_period

    # If the subscription is cancelled and check_date is after the cancellation date, return False
    if hasattr(subscription, 'status') and subscription.status == 'cancelled' and subscription.cancellation_date:
        if check_date > subscription.cancellation_date:
            return False

    if renewal_period == 'weekly':
        # For weekly, check if this day is a renewal date
        current_date = start_date
        while current_date <= check_date:
            if current_date == check_date:
                return True
            current_date += timedelta(days=7)
        return False

    elif renewal_period == 'monthly':
        # For monthly, check if the day of the month matches
        if start_date.day == check_date.day and check_date >= start_date:
            return True

        # Check if it's the last day of the month and the subscription's day doesn't exist in this month
        last_day_current_month = calendar.monthrange(check_date.year, check_date.month)[1]
        if check_date.day == last_day_current_month and check_date >= start_date:
            # If the start day is greater than the last day of the current month,
            # this is a renewal date
            if start_date.day > last_day_current_month:
                return True

        return False

    elif renewal_period == 'quarterly':
        # For quarterly, check if this is a quarterly renewal date
        months_since_start = (check_date.year - start_date.year) * 12 + check_date.month - start_date.month

        if months_since_start % 3 == 0:
            # Check if the day of the month matches
            if start_date.day == check_date.day and check_date >= start_date:
                return True

            # Check if it's the last day of the month and the subscription's day doesn't exist in this month
            last_day_current_month = calendar.monthrange(check_date.year, check_date.month)[1]
            if check_date.day == last_day_current_month and check_date >= start_date:
                # If the start day is greater than the last day of the current month,
                # this is a renewal date
                if start_date.day > last_day_current_month:
                    return True

        return False

    elif renewal_period == 'yearly':
        # For yearly, check if the month and day match
        if start_date.month == check_date.month:
            # Check if the day of the month matches
            if start_date.day == check_date.day and check_date >= start_date:
                return True

            # Check if it's the last day of the month and the subscription's day doesn't exist in this month
            last_day = calendar.monthrange(check_date.year, check_date.month)[1]
            if check_date.day == last_day and check_date >= start_date:
                # If the start day is greater than the last day of this month,
                # this is a renewal date
                if start_date.day > last_day:
                    return True

        return False

    elif renewal_period == 'biennial':
        # For biennial, check if the month and day match and if this is a biennial year
        years_since_start = check_date.year - start_date.year
        if years_since_start % 2 == 0 and start_date.month == check_date.month:
            # Check if the day of the month matches
            if start_date.day == check_date.day and check_date >= start_date:
                return True

            # Check if it's the last day of the month and the subscription's day doesn't exist in this month
            last_day = calendar.monthrange(check_date.year, check_date.month)[1]
            if check_date.day == last_day and check_date >= start_date:
                # If the start day is greater than the last day of this month,
                # this is a renewal date
                if start_date.day > last_day:
                    return True

        return False

    return False

def generate_subscriptions_csv(subscriptions):
    """
    Generate a CSV file from a queryset of subscriptions.

    Args:
        subscriptions: A queryset of Subscription objects

    Returns:
        A string containing the CSV data
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow(['name', 'category', 'cost', 'currency', 'renewal_period', 'start_date', 'url', 'notes'])

    # Write data rows
    for subscription in subscriptions:
        category_name = subscription.category.name if subscription.category else ''
        writer.writerow([
            subscription.name,
            category_name,
            subscription.cost,
            subscription.currency,
            subscription.renewal_period,
            subscription.start_date.isoformat(),
            subscription.url or '',
            subscription.notes or ''
        ])

    return output.getvalue()

def parse_subscriptions_csv(csv_file):
    """
    Parse a CSV file containing subscription data.

    Args:
        csv_file: A file-like object containing CSV data

    Returns:
        A list of dictionaries, each representing a subscription
    """
    reader = csv.DictReader(csv_file)
    subscriptions = []

    for row in reader:
        # Convert empty strings to None
        for key, value in row.items():
            if value == '':
                row[key] = None

        # Parse date
        if row.get('start_date'):
            try:
                row['start_date'] = datetime.fromisoformat(row['start_date']).date()
            except ValueError:
                # If date parsing fails, use current date
                row['start_date'] = datetime.now().date()

        subscriptions.append(row)

    return subscriptions

def generate_categories_csv(categories):
    """
    Generate a CSV file from a queryset of categories.

    Args:
        categories: A queryset of Category objects

    Returns:
        A string containing the CSV data
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow(['name'])

    # Write data rows
    for category in categories:
        writer.writerow([category.name])

    return output.getvalue()

def parse_categories_csv(csv_file):
    """
    Parse a CSV file containing category data.

    Args:
        csv_file: A file-like object containing CSV data

    Returns:
        A list of dictionaries, each representing a category
    """
    reader = csv.DictReader(csv_file)
    categories = []

    for row in reader:
        # Convert empty strings to None
        for key, value in row.items():
            if value == '':
                row[key] = None

        categories.append(row)

    return categories

def generate_currencies_csv(currencies):
    """
    Generate a CSV file from a queryset of currencies.

    Args:
        currencies: A queryset of Currency objects

    Returns:
        A string containing the CSV data
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow(['code', 'name', 'symbol', 'is_default'])

    # Write data rows
    for currency in currencies:
        writer.writerow([
            currency.code,
            currency.name,
            currency.symbol,
            currency.is_default
        ])

    return output.getvalue()

def parse_currencies_csv(csv_file):
    """
    Parse a CSV file containing currency data.

    Args:
        csv_file: A file-like object containing CSV data

    Returns:
        A list of dictionaries, each representing a currency
    """
    reader = csv.DictReader(csv_file)
    currencies = []

    for row in reader:
        # Convert empty strings to None
        for key, value in row.items():
            if value == '':
                row[key] = None

        # Convert is_default to boolean
        if 'is_default' in row:
            if row['is_default'] in ['True', 'true', '1', 'yes', 'Yes']:
                row['is_default'] = True
            else:
                row['is_default'] = False

        currencies.append(row)

    return currencies

def get_next_billing_date(subscription):
    """
    Calculate the next billing date for a subscription from today.
    If the subscription is cancelled, returns None if today is after the cancellation date.

    Args:
        subscription: A Subscription object

    Returns:
        A datetime.date object representing the next billing date, or None if the subscription is cancelled
        and today is after the cancellation date.
    """
    from datetime import date
    today = date.today()
    start_date = subscription.start_date
    renewal_period = subscription.renewal_period

    # If the subscription is cancelled and today is after the cancellation date, return None
    if hasattr(subscription, 'status') and subscription.status == 'cancelled' and subscription.cancellation_date:
        if today > subscription.cancellation_date:
            return None

    if renewal_period == 'weekly':
        # For weekly, find the next weekly date from today
        days_since_start = (today - start_date).days
        days_until_next = 7 - (days_since_start % 7)
        if days_until_next == 7:
            days_until_next = 0
        return today + timedelta(days=days_until_next)

    elif renewal_period == 'monthly':
        # For monthly, find the next occurrence of the start day
        next_date = today.replace(day=1)  # Start from the first day of the current month

        while True:
            # Try to set the day to the start day
            try:
                next_date = next_date.replace(day=start_date.day)
            except ValueError:
                # If the day doesn't exist in this month, use the last day
                last_day = calendar.monthrange(next_date.year, next_date.month)[1]
                next_date = next_date.replace(day=last_day)

            # If the date is in the future, we found our next billing date
            if next_date >= today:
                return next_date

            # Otherwise, move to the next month
            if next_date.month == 12:
                next_date = next_date.replace(year=next_date.year + 1, month=1, day=1)
            else:
                next_date = next_date.replace(month=next_date.month + 1, day=1)

    elif renewal_period == 'quarterly':
        # For quarterly, find the next quarterly date from the start date
        next_date = today.replace(day=1)  # Start from the first day of the current month

        while True:
            # Calculate months since start
            months_since_start = (next_date.year - start_date.year) * 12 + next_date.month - start_date.month

            # If this is a quarterly month (0, 3, 6, 9 months from start)
            if months_since_start % 3 == 0:
                # Try to set the day to the start day
                try:
                    next_date = next_date.replace(day=start_date.day)
                except ValueError:
                    # If the day doesn't exist in this month, use the last day
                    last_day = calendar.monthrange(next_date.year, next_date.month)[1]
                    next_date = next_date.replace(day=last_day)

                # If the date is in the future, we found our next billing date
                if next_date >= today:
                    return next_date

            # Move to the next month
            if next_date.month == 12:
                next_date = next_date.replace(year=next_date.year + 1, month=1, day=1)
            else:
                next_date = next_date.replace(month=next_date.month + 1, day=1)

    elif renewal_period == 'yearly':
        # For yearly, find the next yearly date from the start date
        next_date = today.replace(month=start_date.month, day=1)

        # If we're already past this year's date, move to next year
        if today.month > start_date.month or (today.month == start_date.month and today.day > start_date.day):
            next_date = next_date.replace(year=today.year + 1)
        else:
            next_date = next_date.replace(year=today.year)

        # Try to set the day to the start day
        try:
            next_date = next_date.replace(day=start_date.day)
        except ValueError:
            # If the day doesn't exist in this month, use the last day
            last_day = calendar.monthrange(next_date.year, next_date.month)[1]
            next_date = next_date.replace(day=last_day)

        return next_date

    elif renewal_period == 'biennial':
        # For biennial, find the next biennial date from the start date
        next_date = today.replace(month=start_date.month, day=1)

        # Calculate years since start
        years_since_start = today.year - start_date.year

        # If we're in a biennial year but haven't reached the date yet
        if years_since_start % 2 == 0 and (today.month < start_date.month or 
                                          (today.month == start_date.month and today.day < start_date.day)):
            next_date = next_date.replace(year=today.year)
        else:
            # Move to the next biennial year - always add 2 years to ensure biennial renewals
            next_year = today.year + (2 - (years_since_start % 2))
            next_date = next_date.replace(year=next_year)

        # Try to set the day to the start day
        try:
            next_date = next_date.replace(day=start_date.day)
        except ValueError:
            # If the day doesn't exist in this month, use the last day
            last_day = calendar.monthrange(next_date.year, next_date.month)[1]
            next_date = next_date.replace(day=last_day)

        return next_date

    # Default fallback
    return start_date
