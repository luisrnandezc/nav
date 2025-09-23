from django import template

register = template.Library()


@register.filter
def getitem(mapping, key):
    try:
        return mapping.get(key)
    except Exception:
        return None


