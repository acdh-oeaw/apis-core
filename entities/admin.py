from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from .models import Person, Place, Institution, Event, Work


class BaseEntitiesAdmin(CompareVersionAdmin):
    exclude = ('text',)

admin.site.register(Work)
admin.site.register(Person, BaseEntitiesAdmin)
admin.site.register(Place, BaseEntitiesAdmin)
admin.site.register(Institution, BaseEntitiesAdmin)
admin.site.register(Event, BaseEntitiesAdmin)
