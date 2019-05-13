from apis_core.apis_entities.api_views import (
    EventViewSet,
    InstitutionViewSet,
    NetJsonViewSet,
    PersonViewSet,
    PlaceGeoJsonViewSet,
    PlaceViewSet,
    WorkViewSet,
)

# from rest_framework_swagger.views import get_swagger_view
# from entities.views2 import GenericEntitiesCreateStanbolView
from apis_core.apis_metainfo.api_views import (
    CollectionViewSet,
    SourceSerializerViewSet,
    TempEntityClassViewSet,
    TextViewSet,
    UriSerializerViewSet,
)
from apis_core.apis_relations.api_views import (
    EventEventViewSet,
    EventWorkViewSet,
    InstitutionEventViewSet,
    InstitutionInstitutionViewSet,
    InstitutionPlaceViewSet,
    InstitutionWorkViewSet,
    PersonEventViewSet,
    PersonInstitutionViewSet,
    PersonPersonViewSet,
    PersonPlaceViewSet,
    PersonWorkViewSet,
    PlaceEventViewSet,
    PlacePlaceViewSet,
    PlaceWorkViewSet,
    WorkWorkViewSet,
)
from apis_core.apis_vocabularies.api_views import (
    CollectionTypeViewSet,
    EventEventRelationViewSet,
    EventTypeViewSet,
    EventWorkRelationViewSet,
    InstitutionEventRelationViewSet,
    InstitutionInstitutionRelationViewSet,
    InstitutionPlaceRelationViewSet,
    InstitutionTypeViewSet,
    InstitutionWorkRelationViewSet,
    PersonEventRelationViewSet,
    PersonInstitutionRelationViewSet,
    PersonPersonRelationViewSet,
    PersonPlaceRelationViewSet,
    PersonWorkRelationViewSet,
    PlaceEventRelationViewSet,
    PlacePlaceRelationViewSet,
    PlaceTypeViewSet,
    PlaceWorkRelationViewSet,
    ProfessionTypeViewSet,
    TextTypeViewSet,
    UserViewSet,
    VocabNamesViewSet,
    VocabsBaseClassViewSet,
    WorkTypeViewSet,
    WorkWorkRelationViewSet,
)
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.views.static import serve
from rest_framework import routers

from .api_routers import create_generic_api_viewset

app_name = "apis_core"

router = routers.DefaultRouter()
for app_label in ["entities", "metainfo", "vocabularies", "relations"]:
    for ent in ContentType.objects.filter(app_label="apis_{}".format(app_label)):
        name = "".join([x.title() for x in ent.name.split(" ")])
        try:
            router.register(
                r"{}/{}".format(app_label, name.lower()),
                create_generic_api_viewset(
                    entity=name, app_label="apis_{}".format(app_label)
                ),
            )
        except AttributeError:
            print("{} not found, skipping".format(name.lower()))


if "apis_highlighter" in settings.INSTALLED_APPS:
    from apis_highlighter.api_views import (
        HighlighterProjectViewSet,
        HighlighterTextHighViewSet,
        HighlighterMenuEntryViewSet,
        HighlighterHighlightTextViewSet,
        HighlighterVocabularyAPIViewSet,
        HighlighterAnnotationViewSet,
    )

    router.register(r"HLProjects", HighlighterProjectViewSet)
    router.register(r"HLTextHigh", HighlighterTextHighViewSet)
    router.register(r"HLMenuEntry", HighlighterMenuEntryViewSet)
    router.register(
        r"HLTextHighlighter", HighlighterHighlightTextViewSet, "HLTextHighlighter"
    )
    router.register(r"HLVocabularyAPI", HighlighterVocabularyAPIViewSet)
    router.register(r"HLAnnotation", HighlighterAnnotationViewSet)

router.register(r"users", UserViewSet)
router.register(r"GeoJsonPlace", PlaceGeoJsonViewSet, "PlaceGeoJson")
router.register(r"NetJson", NetJsonViewSet, "NetJson")

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"labels/", include("apis_core.apis_labels.urls", namespace="apis_labels")),
    url(r"tei/", include("apis_core.apis_tei.tei_urls", namespace="apis_tei")),
    url(
        r"entities/", include("apis_core.apis_entities.urls", namespace="apis_entities")
    ),
    url(r"visuals/", include("apis_core.apis_vis.urls", namespace="apis_visuals")),
    url(
        r"relations/",
        include("apis_core.apis_relations.urls", namespace="apis_relations"),
    ),
    url(
        r"vocabularies/",
        include("apis_core.apis_vocabularies.urls", namespace="apis_vocabularies"),
    ),
    # url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(
        r"^api/", include((router.urls, "apis_core"), namespace="apis_api")
    ),  # routers do not support namespaces out of the box
    url(r"^api2/", include("apis_core.apis_entities.api_urls", namespace="apis_api2")),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    # url(r'^api-schema/', schema_view),
    url(r"^apis-vis/", include("apis_core.apis_vis.urls", namespace="apis_vis")),
    url(
        r"^docs/(?P<path>.*)",
        login_required(serve),
        {"document_root": "apis-core/docs/_build/html"},
        "docs",
    ),
    # url(r'^docs/', include('sphinxdoc.urls')),
    # url(r'^accounts/', include('registration.backends.simple.urls')),
]

if "apis_highlighter" in settings.INSTALLED_APPS:
    urlpatterns.append(
        url(r"highlighter/", include("apis_highlighter.urls", namespace="highlighter"))
    )

if "apis_fulltext_download" in settings.INSTALLED_APPS:
    urlpatterns.append(
        url(
            r"fulltext_download/",
            include("apis_fulltext_download.urls", namespace="apis_fulltext_download"),
        )
    )

if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [url(r"^__debug__/", include(debug_toolbar.urls))] + urlpatterns
