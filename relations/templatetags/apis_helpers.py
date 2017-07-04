from django import template

register = template.Library()

@register.filter
def content_type(obj):
    if not obj:
        return False
    return obj.__class__.__name__