from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary by key
    Usage: {{ mydict|get_item:key_variable }}
    """
    if dictionary is None:
        return None
    
    # Try both integer and string keys
    try:
        int_key = int(key)
        return dictionary.get(int_key, dictionary.get(str(key)))
    except (ValueError, TypeError):
        return dictionary.get(str(key))

@register.filter
def get_health_color(health):
    """Returns a color based on project health status"""
    if health == 'poor':
        return '#ef4444'  # Red
    elif health == 'needs_work':
        return '#f59e0b'  # Amber
    elif health == 'good':
        return '#10b981'  # Green
    return '#9ca3af'  # Default gray

@register.filter
def get_health_percentage(health):
    """Converts health status to a percentage value for sliders"""
    if health == 'poor':
        return 20
    elif health == 'needs_work':
        return 50
    elif health == 'good':
        return 85
    return 50  # Default middle value

@register.filter
def get_status_badge_color(status):
    """Returns a color for status badges"""
    status_colors = {
        'active': '#3b82f6',      # Blue
        'completed': '#10b981',   # Green
        'on_hold': '#f59e0b',     # Amber
        'cancelled': '#ef4444',   # Red
        'completed_early': '#8b5cf6' # Purple
    }
    return status_colors.get(status, '#9ca3af')  # Default to gray 