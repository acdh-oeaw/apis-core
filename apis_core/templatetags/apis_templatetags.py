from django import template
register = template.library()

@register.inclusion_tag('apis_templatetag.html', takes_context=True)
def apis_base_templatetag(context):
   values = {}
   return values
