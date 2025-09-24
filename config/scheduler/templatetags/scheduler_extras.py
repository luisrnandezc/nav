from django import template

register = template.Library()

@register.filter
def chunk_list(value, chunk_size):
    """Split a list into chunks of specified size."""
    chunk_size = int(chunk_size)
    for i in range(0, len(value), chunk_size):
        yield value[i:i + chunk_size]