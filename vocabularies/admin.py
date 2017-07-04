from django.contrib import admin

from .models import (
    ProfessionType, PlaceType, PersonPlaceRelation,
    PersonPersonRelation, PersonInstitutionRelation, InstitutionType,
    EventType, PersonEventRelation, Title, VocabsBaseClass, LabelType,
    InstitutionInstitutionRelation, TextType, InstitutionPlaceRelation,
    PlacePlaceRelation, VocabsUri, CollectionType,
    InstitutionEventRelation, PlaceEventRelation, PersonWorkRelation,
    InstitutionWorkRelation, PlaceWorkRelation, EventWorkRelation
    )


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


admin.site.register(ProfessionType, BaseAdminVocabularies)
admin.site.register(PlaceType, BaseAdminVocabularies)
admin.site.register(LabelType, BaseAdminVocabularies)
admin.site.register(EventType, BaseAdminVocabularies)
admin.site.register(Title, BaseAdminVocabularies)
admin.site.register(InstitutionType, BaseAdminVocabularies)
admin.site.register(PersonPlaceRelation, BaseAdminVocabularies)
admin.site.register(PersonPersonRelation, BaseAdminVocabularies)
admin.site.register(PersonInstitutionRelation, BaseAdminVocabularies)
admin.site.register(PersonEventRelation, BaseAdminVocabularies)
admin.site.register(InstitutionInstitutionRelation, BaseAdminVocabularies)
admin.site.register(TextType, BaseAdminVocabularies)
admin.site.register(InstitutionPlaceRelation, BaseAdminVocabularies)
admin.site.register(PlacePlaceRelation, BaseAdminVocabularies)
admin.site.register(VocabsUri, BaseAdminVocabularies)
admin.site.register(InstitutionEventRelation, BaseAdminVocabularies)
admin.site.register(PlaceEventRelation, BaseAdminVocabularies)
admin.site.register(PersonWorkRelation, BaseAdminVocabularies)
admin.site.register(InstitutionWorkRelation, BaseAdminVocabularies)
admin.site.register(PlaceWorkRelation, BaseAdminVocabularies)
admin.site.register(EventWorkRelation, BaseAdminVocabularies)

admin.site.register(CollectionType)
