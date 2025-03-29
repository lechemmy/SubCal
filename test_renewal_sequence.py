from datetime import date
from subscriptions.utils import calculate_next_renewal_date

# Test the sequence of renewal dates for a subscription starting on January 30th
start_date = date(2023, 1, 30)
renewal_period = 'monthly'

# Calculate renewal dates for February 2023
feb_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 2)
print(f"February 2023 renewal dates: {feb_dates}")

# Calculate renewal dates for March 2023
mar_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 3)
print(f"March 2023 renewal dates: {mar_dates}")

# Calculate renewal dates for April 2023
apr_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 4)
print(f"April 2023 renewal dates: {apr_dates}")

# Calculate renewal dates for May 2023
may_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 5)
print(f"May 2023 renewal dates: {may_dates}")