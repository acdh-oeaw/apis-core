from django.contrib import admin

from .models import Source, Collection, Text, Uri


admin.site.register(Source)
admin.site.register(Collection)
admin.site.register(Text)
admin.site.register(Uri)



