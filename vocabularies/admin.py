from django.contrib import admin
from django.apps import apps


class BaseAdminVocabularies(admin.ModelAdmin):
    '''Base class used to store the User foreign key in the background when someone adds a vocab.'''

    exclude = ('userAdded',)

    def get_fields(self, request, obj=None):
        lst = super(BaseAdminVocabularies, self).get_fields(request, obj=None)
        if not request.user.is_superuser:
            lst.remove('status')
        return lst

    def get_queryset(self, request):
        qs = super(BaseAdminVocabularies, self).get_queryset(request)
        if request.user.is_superuser:
            return qs.all()
        return qs.filter(userAdded__groups__in=request.user.groups.all()).distinct()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.userAdded = request.user
        obj.save()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        qs = super(BaseAdminVocabularies, self).get_queryset(request)
        if db_field.name == "parent_class" and request.user.is_superuser:
            kwargs["queryset"] = qs.all()
        elif db_field.name == "parent_class":
            kwargs["queryset"] = qs.filter(userAdded__groups__in=request.user.groups.all())
        return super(BaseAdminVocabularies, self).formfield_for_foreignkey(db_field, request, **kwargs)


app = apps.get_app_config('vocabularies')

for model_name, model in app.models.items():
    admin.site.register(model)

