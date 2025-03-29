from datetime import date
from subscriptions.utils import calculate_next_renewal_date

# Test for February 30th directly
# We can't create a date object with February 30th, so we'll use a different approach
# We'll create a subscription that starts on January 30th and check if it correctly renews on March 1st for February

# Create a subscription that starts on January 30th
start_date = date(2023, 1, 30)
renewal_period = 'monthly'

# Calculate renewal date for February (which doesn't have a 30th day)
# This should be March 1st, not February 1st
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 2)
print(f"Renewal dates for February: {renewal_dates}")

# Let's also check what happens if we try to calculate the renewal date for a month
# where the subscription's day exists
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 3)
print(f"Renewal dates for March: {renewal_dates}")

# Let's also check what happens if we try to calculate the renewal date for a month
# where the subscription's day is the last day of the month
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 4)
print(f"Renewal dates for April: {renewal_dates}")