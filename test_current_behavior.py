from datetime import date
from subscriptions.utils import calculate_next_renewal_date

# Test for January 30th subscription
start_date = date(2023, 1, 30)
renewal_period = 'monthly'

# Calculate renewal date for February 2023 (which doesn't have a 30th day)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 2)
print(f"Current behavior - Renewal dates for February 2023: {renewal_dates}")

# Calculate renewal date for March 2023 (which has a 31st day)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 3)
print(f"Current behavior - Renewal dates for March 2023: {renewal_dates}")

# Test for January 31st subscription
start_date = date(2023, 1, 31)
renewal_period = 'monthly'

# Calculate renewal date for February 2023 (which doesn't have a 31st day)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 2)
print(f"Current behavior - Renewal dates for February 2023 (31st): {renewal_dates}")

# Calculate renewal date for April 2023 (which has 30 days)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 4)
print(f"Current behavior - Renewal dates for April 2023 (31st): {renewal_dates}")