from django import template
register = template.Library()


@register.inclusion_tag('apis_entities/tags/apis_templatetag.html', takes_context=True)
def apis_base_templatetag(context):
    values = {}
    return values
