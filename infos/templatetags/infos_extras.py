from django import template
from infos.models import ProjectInst

register = template.Library()


@register.simple_tag
def project_insts():

    """returns all Project Institution objects"""
    project_insts = ProjectInst.objects.all()
    return project_insts
