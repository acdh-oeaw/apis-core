from django import template
register = template.Library()


@register.inclusion_tag('apis_entities/apis_create_entities.html', takes_context=True)
def apis_create_entities(context):
    values = {}
    return values
