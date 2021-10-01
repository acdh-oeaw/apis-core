from django.contrib import admin
from csvexport.actions import csvexport


from .models import Label


# Register your models here.
class BaseAdmin(admin.ModelAdmin):
    
    search_fields = ('label',)
    list_filter = (
        "isoCode_639_3",
        "label_type",
    )
    list_display = ('label', 'temp_entity', )
    exclude = ('temp_entity', )
    actions = [csvexport]

admin.site.register(Label, BaseAdmin)