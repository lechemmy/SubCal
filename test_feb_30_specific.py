from datetime import date
from subscriptions.utils import calculate_next_renewal_date

# Test for February 30th specifically
# Create a subscription that starts on January 30th
start_date = date(2023, 1, 30)
renewal_period = 'monthly'

# Calculate renewal date for February (which doesn't have a 30th day)
# This should be March 1st, not February 1st
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 2)
print(f"Renewal dates for February: {renewal_dates}")

# Try with a different year to make sure it's consistent
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2024, 2)  # 2024 is a leap year
print(f"Renewal dates for February 2024 (leap year): {renewal_dates}")

# Try with a different month that doesn't have 30 days (February is the only one)
# No need to test again as we already tested February
