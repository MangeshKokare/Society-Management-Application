from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a variable key"""
    if dictionary is None:
        return None
    return dictionary.get(key)

from django import template

register = template.Library()

@register.filter
def get(dictionary, key):
    """
    Get value from dictionary using key
    Usage: {{ mydict|get:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def get_item(dictionary, key):
    """
    Alternative name for get filter
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)