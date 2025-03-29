from datetime import date
from subscriptions.utils import calculate_next_renewal_date

# Test for January 30th subscription
start_date = date(2023, 1, 30)
renewal_period = 'monthly'

# Calculate renewal date for February 2023
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 2)
print(f"Renewal dates for February 2023: {renewal_dates}")

# Calculate renewal date for January 2024
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2024, 1)
print(f"Renewal dates for January 2024: {renewal_dates}")

# Calculate renewal date for February 2024 (leap year)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2024, 2)
print(f"Renewal dates for February 2024 (leap year): {renewal_dates}")