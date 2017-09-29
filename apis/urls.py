from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from entities.api_views import (
    InstitutionViewSet, PersonViewSet, PlaceViewSet, EventViewSet, WorkViewSet, PlaceGeoJsonViewSet,
    NetJsonViewSet
)
from django.views.static import serve
from django.contrib.auth.decorators import login_required
#from rest_framework_swagger.views import get_swagger_view
from metainfo.api_views import (
    CollectionViewSet, TextViewSet, SourceSerializerViewSet,
    UriSerializerViewSet, TempEntityClassViewSet)
from relations.api_views import (
    InstitutionInstitutionViewSet, InstitutionPlaceViewSet, InstitutionEventViewSet, InstitutionWorkViewSet,
    PersonInstitutionViewSet, PersonPlaceViewSet, PersonPersonViewSet, PersonEventViewSet, PersonWorkViewSet,
    PlaceWorkViewSet, PlaceEventViewSet, EventWorkViewSet, EventEventViewSet, WorkWorkViewSet,
    PlacePlaceViewSet)
from vocabularies.api_views import (
    UserViewSet, VocabNamesViewSet, TextTypeViewSet, CollectionTypeViewSet, VocabsBaseClassViewSet,
    InstitutionTypeViewSet, ProfessionTypeViewSet, PlaceTypeViewSet, EventTypeViewSet, WorkTypeViewSet,
    PersonInstitutionRelationViewSet, PersonPlaceRelationViewSet, PersonEventRelationViewSet, PersonWorkRelationViewSet,
    PersonPersonRelationViewSet, InstitutionInstitutionRelationViewSet, InstitutionPlaceRelationViewSet,
    InstitutionEventRelationViewSet, InstitutionWorkRelationViewSet, PlaceEventRelationViewSet,
    PlaceWorkRelationViewSet, EventWorkRelationViewSet, EventEventRelationViewSet, WorkWorkRelationViewSet,
    PlacePlaceRelationViewSet)
from highlighter.api_views import (
    HighlighterProjectViewSet, HighlighterTextHighViewSet, HighlighterMenuEntryViewSet,
    HighlighterHighlightTextViewSet, HighlighterVocabularyAPIViewSet, HighlighterAnnotationViewSet
)
from entities.views import ReversionCompareView
from autocomplete_light import shortcuts as al
al.autodiscover()


#schema_view = get_swagger_view(title='Apis API')

router = routers.DefaultRouter()
router.register(r'tempentity', TempEntityClassViewSet)
router.register(r'institution', InstitutionViewSet)
router.register(r'person', PersonViewSet)
router.register(r'place', PlaceViewSet)
router.register(r'event', EventViewSet)
router.register(r'work', WorkViewSet)
router.register(r'collection', CollectionViewSet)
router.register(r'text', TextViewSet, 'text')
router.register(r'source', SourceSerializerViewSet)
router.register(r'uri', UriSerializerViewSet)
router.register(r'institutionInstitution', InstitutionInstitutionViewSet)
router.register(r'institutioninstitutionrelation', InstitutionInstitutionRelationViewSet)
router.register(r'institutionPlace', InstitutionPlaceViewSet)
router.register(r'institutionplacerelation', InstitutionPlaceRelationViewSet)
router.register(r'institutionEvent', InstitutionEventViewSet)
router.register(r'institutioneventrelation', InstitutionEventRelationViewSet)
router.register(r'institutionWork', InstitutionWorkViewSet)
router.register(r'institutionworkrelation', InstitutionWorkRelationViewSet)
router.register(r'personInstitution', PersonInstitutionViewSet)
router.register(r'personinstitutionrelation', PersonInstitutionRelationViewSet)
router.register(r'personPlace', PersonPlaceViewSet)
router.register(r'personplacerelation', PersonPlaceRelationViewSet)
router.register(r'personEvent', PersonEventViewSet)
router.register(r'personeventrelation', PersonEventRelationViewSet)
router.register(r'personWork', PersonWorkViewSet)
router.register(r'personworkrelation', PersonWorkRelationViewSet)
router.register(r'personPerson', PersonPersonViewSet)
router.register(r'personpersonrelation', PersonPersonRelationViewSet)
router.register(r'placeWork', PlaceWorkViewSet)
router.register(r'placeworkrelation', PlaceWorkRelationViewSet)
router.register(r'placeEvent', PlaceEventViewSet)
router.register(r'placeeventrelation', PlaceEventRelationViewSet)
router.register(r'placePlace', PlacePlaceViewSet)
router.register(r'placeplacerelation', PlacePlaceRelationViewSet)
router.register(r'eventWork', EventWorkViewSet)
router.register(r'eventworkrelation', EventWorkRelationViewSet)
router.register(r'eventEvent', EventEventViewSet)
router.register(r'eventeventrelation', EventEventRelationViewSet)
router.register(r'workWork', WorkWorkViewSet)
router.register(r'workworkrelation', WorkWorkRelationViewSet)
router.register(r'texttype', TextTypeViewSet)
router.register(r'collectiontype', CollectionTypeViewSet)
router.register(r'vocabsbaseclass', VocabsBaseClassViewSet)
router.register(r'institutiontype', InstitutionTypeViewSet)
router.register(r'professiontype', ProfessionTypeViewSet)
router.register(r'placetype', PlaceTypeViewSet)
router.register(r'eventtype', EventTypeViewSet)
router.register(r'worktype', WorkTypeViewSet)
router.register(r'HLProjects', HighlighterProjectViewSet)
router.register(r'HLTextHigh', HighlighterTextHighViewSet)
router.register(r'HLMenuEntry', HighlighterMenuEntryViewSet)
router.register(r'HLTextHighlighter', HighlighterHighlightTextViewSet, 'HLTextHighlighter')
router.register(r'HLVocabularyAPI', HighlighterVocabularyAPIViewSet)
router.register(r'HLAnnotation', HighlighterAnnotationViewSet)
router.register(r'users', UserViewSet)
router.register(r'GeoJsonPlace', PlaceGeoJsonViewSet, 'PlaceGeoJson')
router.register(r'NetJson', NetJsonViewSet, 'NetJson')
router.register(r'VocabNames', VocabNamesViewSet)


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'labels/', include('labels.urls', namespace='labels')),
    url(r'entities/', include('entities.urls', namespace='entities')),
    url(r'highlighter/', include('highlighter.urls', namespace='highlighter')),
    url(r'relations/', include('relations.urls', namespace='relations')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^api/', include(router.urls)),    #routers do not support namespaces out of the box
    url(r'^api2/', include('entities.api_urls', namespace="api2")),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    #url(r'^api-schema/', schema_view),
    url(r'^docs/(?P<path>.*)', login_required(serve), {'document_root': 'apis-core/docs/_build/html'}, 'docs'),
    #url(r'^docs/', include('sphinxdoc.urls')),
    url(r'^compare/(?P<app>[a-z]+)/(?P<kind>[a-z]+)/(?P<pk>\d+)$', ReversionCompareView.as_view() ),
    url(r'^', include('webpage.urls', namespace='webpage')),
    url(r'^accounts/', include('registration.backends.simple.urls')),
]
