from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.urls import path
from django.views.static import serve
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import response, schemas
from rest_framework import routers
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.schemas import get_schema_view

from apis_core.api_routers import views
from apis_core.apis_entities.api_views import (
    NetJsonViewSet,
    PlaceGeoJsonViewSet,
)
from apis_core.apis_vocabularies.api_views import UserViewSet
from apis_core.helper_functions.ContentType import GetContentTypes

app_name = "apis_core"

router = routers.DefaultRouter()
for app_label, ent in GetContentTypes().get_names():
    try:
        router.register(
            r"{}/{}".format(app_label.split("_")[1], ent.lower()),
            views[ent.lower()],
            ent.lower(),
        )
    except Exception as e:
        print("{} not found, skipping".format(ent.lower()))


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
    # router.register(
    #    r"HLTextHighlighter", HighlighterHighlightTextViewSet, "HLTextHighlighter"
    # )
    # router.register(r"HLVocabularyAPI", HighlighterVocabularyAPIViewSet)
    # router.register(r"HLAnnotation", HighlighterAnnotationViewSet)

router.register(r"users", UserViewSet)
router.register(r"GeoJsonPlace", PlaceGeoJsonViewSet, "PlaceGeoJson")
# router.register(r"NetJson", NetJsonViewSet, "NetJson")


from rest_framework import permissions

# from drf_yasg.views import get_schema_view as get_schema_view2
# from drf_yasg import openapi
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


# schema_view2 = get_schema_view2(
#   openapi.Info(
#      title="APIS API",
#      default_version='v1',
#      description="Hyperlinked API of the APIS Framework",
# terms_of_service="https://www.google.com/policies/terms/",
#      contact=openapi.Contact(email="matthias.schloegl@oeaw.ac.at"),
#      license=openapi.License(name="MIT"),
#   ),
#   public=True,
#   permission_classes=(permissions.AllowAny,),
# )

# class APISSchemaGenerator(OpenAPISchemaGenerator):
#    info = "APIS test"
#    title = "APIS_API v2"

#    def __init__(self, *args, **kwargs):
#        super(APISSchemaGenerator, self).__init__(*args, **kwargs)


# class SchemaViewSwagger(schema_view2):
#    generator_class = APISSchemaGenerator

#    def get_filter_parameters(self, filter_backend):
#       if isinstance(filter_backend, DjangoFilterBackend):
#            result = super(SchemaViewSwagger, self).get_filter_parameters(filter_backend)
#            for param in result:
#                if not param.get('description', ''):
#                    param.description = "Filter the returned list by {field_name}".format(field_name=param.name)

#            return result

#        return NotHandled

#    def get_operation(self, operation_keys):
#        super(SchemaViewSwagger, self).get_operation(operation_keys)

#    def __init__(self, *args, **kwargs):
#        super(SchemaViewSwagger, self).__init__(*args, **kwargs)


def build_apis_mock_request(method, path, view, original_request, **kwargs):
    # default mock request
    request = build_mock_request(method, path, view, original_request, **kwargs)
    # the added wagtail magic
    request.router = router
    return request


urlpatterns = [
    url(r"^admin/", admin.site.urls),
    # url(r'^swagger(?P<format>\.json|\.yaml)$', SchemaViewSwagger.without_ui(cache_timeout=-1), name='schema-json'),
    # url(r'^swagger/$', SchemaViewSwagger.with_ui('swagger', cache_timeout=-1), name='schema-swagger-ui'),
    # url(r'^redoc/$', SchemaViewSwagger.with_ui('redoc', cache_timeout=-1), name='schema-redoc'),
    path("swagger/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "swagger/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="apis_core:schema"),
        name="swagger-ui",
    ),
    path(
        "swagger/schema/redoc/",
        SpectacularRedocView.as_view(url_name="apis_core:schema"),
        name="redoc",
    ),
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
    # path('openapi-2', schema_view),
    # path('openapi-api', get_schema_view(
    #    title="APIS",
    #    description="APIS API schema definition",
    #    urlconf='apis_core.apis_entities.api_urls',
    # ), name='openapi-schema-api'),
    url(r"^api2/", include("apis_core.apis_entities.api_urls", namespace="apis_api2")),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    # url(r'^api-schema/', schema_view),
    url(r"^apis-vis/", include("apis_core.apis_vis.urls", namespace="apis_vis")),
    url(
        r"^docs/(?P<path>.*)$",
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
