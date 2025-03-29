from datetime import date
from subscriptions.utils import calculate_next_renewal_date

# Test for January 30th subscription
start_date = date(2023, 1, 30)
renewal_period = 'monthly'

# Calculate renewal date for February 2023 (which doesn't have a 30th day)
# Should be February 28th, 2023 (the last day of February 2023)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 2)
print(f"New behavior - Renewal dates for February 2023: {renewal_dates}")

# Calculate renewal date for March 2023 (which has a 31st day)
# Should still be March 30th, 2023
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 3)
print(f"New behavior - Renewal dates for March 2023: {renewal_dates}")

# Test for January 31st subscription
start_date = date(2023, 1, 31)
renewal_period = 'monthly'

# Calculate renewal date for February 2023 (which doesn't have a 31st day)
# Should be February 28th, 2023 (the last day of February 2023)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 2)
print(f"New behavior - Renewal dates for February 2023 (31st): {renewal_dates}")

# Calculate renewal date for April 2023 (which has 30 days)
# Should be April 30th, 2023 (the last day of April 2023)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2023, 4)
print(f"New behavior - Renewal dates for April 2023 (31st): {renewal_dates}")

# Test for February 29th, 2020 (leap year) subscription
start_date = date(2020, 2, 29)
renewal_period = 'monthly'

# Calculate renewal date for February 2021 (which doesn't have a 29th day)
# Should be February 28th, 2021 (the last day of February 2021)
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2021, 2)
print(f"New behavior - Renewal dates for February 2021 (leap year): {renewal_dates}")

# Calculate renewal date for February 2024 (which is a leap year)
# Should be February 29th, 2024
renewal_dates = calculate_next_renewal_date(start_date, renewal_period, 2024, 2)
print(f"New behavior - Renewal dates for February 2024 (leap year): {renewal_dates}")