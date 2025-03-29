from datetime import date
from subscriptions.utils import calculate_next_renewal_date

# Test for February 30th
# Create a subscription that starts on January 30th
start_date = date(2023, 1, 30)
renewal_period = 'monthly'

# Calculate renewal date for February (which doesn't have a 30th day)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 2)
print(f"Renewal dates for February: {renewal_dates}")

# Calculate renewal date for March (which has a 31st day)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 3)
print(f"Renewal dates for March: {renewal_dates}")

# Calculate renewal date for April (which has a 30th day)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 4)
print(f"Renewal dates for April: {renewal_dates}")