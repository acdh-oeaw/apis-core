from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from .models import Person, Place, Institution, Event


class BaseEntitiesAdmin(CompareVersionAdmin):
    exclude = ('text',)

admin.site.register(Person, BaseEntitiesAdmin)
admin.site.register(Place, BaseEntitiesAdmin)
admin.site.register(Institution, BaseEntitiesAdmin)
admin.site.register(Event, BaseEntitiesAdmin)
