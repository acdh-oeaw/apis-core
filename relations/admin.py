from django.contrib import admin

from .models import (PersonPlace, PersonPerson, PersonInstitution,
	PersonEvent)

admin.site.register(PersonPlace)
admin.site.register(PersonPerson)
admin.site.register(PersonInstitution)
admin.site.register(PersonEvent)
# Register your models here.
