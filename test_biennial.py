from datetime import date, timedelta
import calendar

# Create a simplified version of the get_next_billing_date function
# that only includes the biennial renewal logic
def get_next_biennial_date(start_date, today):
    """
    Calculate the next biennial billing date from today.

    Args:
        start_date: The start date of the subscription
        today: The current date

    Returns:
        A datetime.date object representing the next billing date
    """
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

# Test cases
def run_test(start_date, today_date, expected_next_date):
    # Calculate the next billing date
    next_date = get_next_biennial_date(start_date, today_date)

    # Check if the result matches the expected date
    if next_date == expected_next_date:
        print(f"✅ Test passed: Start: {start_date}, Today: {today_date}, Next: {next_date}")
    else:
        print(f"❌ Test failed: Start: {start_date}, Today: {today_date}, Expected: {expected_next_date}, Got: {next_date}")

# Test scenarios
print("Testing biennial renewal logic...")

# Scenario 1: Today is before the first renewal
start_date = date(2020, 6, 15)
today_date = date(2022, 5, 1)  # Before the 2-year renewal
expected_next_date = date(2022, 6, 15)  # Should be exactly 2 years after start
run_test(start_date, today_date, expected_next_date)

# Scenario 2: Today is after the first renewal but before the second
start_date = date(2020, 6, 15)
today_date = date(2022, 7, 1)  # After the 2-year renewal
expected_next_date = date(2024, 6, 15)  # Should be exactly 4 years after start
run_test(start_date, today_date, expected_next_date)

# Scenario 3: Today is exactly on a renewal date
start_date = date(2020, 6, 15)
today_date = date(2022, 6, 15)  # Exactly on the 2-year renewal
expected_next_date = date(2024, 6, 15)  # Should be exactly 4 years after start
run_test(start_date, today_date, expected_next_date)

# Scenario 4: Start date in a month with more days than February
start_date = date(2020, 3, 31)
today_date = date(2022, 2, 15)  # Before the 2-year renewal
expected_next_date = date(2022, 3, 31)  # Should be exactly 2 years after start
run_test(start_date, today_date, expected_next_date)

# Scenario 5: Today is in a non-biennial year
start_date = date(2020, 6, 15)
today_date = date(2023, 1, 1)  # In a non-biennial year
expected_next_date = date(2024, 6, 15)  # Should be the next biennial year
run_test(start_date, today_date, expected_next_date)

print("Testing complete.")
