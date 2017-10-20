from django.contrib import admin

from .models import (
    PersonPlace, PersonPerson, PersonInstitution, PersonEvent, WorkWork)

admin.site.register(PersonPlace)
admin.site.register(PersonPerson)
admin.site.register(PersonInstitution)
admin.site.register(PersonEvent)
admin.site.register(WorkWork)
# Register your models here.
