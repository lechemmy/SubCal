from django import template
import calendar

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using a key.
    Usage: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key, [])

@register.filter
def month_name(month_number):
    """
    Get the name of a month from its number (1-12).
    Usage: {{ month_number|month_name }}
    """
    try:
        return calendar.month_name[int(month_number)]
    except (ValueError, IndexError):
        return ""
