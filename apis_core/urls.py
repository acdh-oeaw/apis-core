from rest_framework.decorators import api_view, renderer_classes
from rest_framework import response, schemas
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
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
from django.urls import path
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.views.static import serve
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from .api_routers import create_generic_api_viewset
from rest_framework_swagger.views import get_swagger_view

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
        except Exception as e:
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


@api_view()
@renderer_classes([SwaggerUIRenderer, OpenAPIRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='APIS API')
    return response.Response(generator.get_schema(request=request))


from rest_framework import permissions
from drf_yasg.views import get_schema_view as get_schema_view2
from drf_yasg import openapi


schema_view2 = get_schema_view2(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view2.without_ui(cache_timeout=-1), name='schema-json'),
    url(r'^swagger/$', schema_view2.with_ui('swagger', cache_timeout=-1), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view2.with_ui('redoc', cache_timeout=-1), name='schema-redoc'),
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
    url(
        r"metainfo/",
        include("apis_core.apis_metainfo.urls", namespace="apis_metainfo"),
    ),
    url(
        r"metainfo-ac/",
        include("apis_core.apis_metainfo.dal_urls", namespace="apis_metainfo-ac"),
    ),
    # url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(
        r"^api/", include((router.urls, "apis_core"), namespace="apis_api")
    ),  # routers do not support namespaces out of the box
    path('openapi-2', schema_view),
    path('openapi-api', get_schema_view(
        title="APIS",
        description="APIS API schema definition",
        urlconf='apis_core.apis_entities.api_urls',
    ), name='openapi-schema-api'),
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
