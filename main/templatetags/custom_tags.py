from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def truncate_chars(value, max_length):
    """Truncates a string after a certain number of characters"""
    if len(value) > max_length:
        return value[:max_length] + '...'
    return value

@register.filter
def get_item(dictionary, key):
    """Gets an item from a dictionary using the key"""
    return dictionary.get(key)

@register.simple_tag
def relative_url(value, field_name, urlencode=None):
    """Adds GET parameters to the current URL"""
    url = '?{}={}'.format(field_name, value)
    if urlencode:
        querystring = urlencode.split('&')
        filtered_querystring = filter(lambda p: p.split('=')[0] != field_name, querystring)
        encoded_querystring = '&'.join(filtered_querystring)
        url = '{}&{}'.format(url, encoded_querystring)
    return url 