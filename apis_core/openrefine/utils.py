from django.conf import settings

APIS_BASE_URI = settings.APIS_BASE_URI
PROJECT_NAME = settings.PROJECT_NAME


def get_properties():
    data = [
        {"id": "name", "name": "last name (exact string match)"},
        {"id": "name__icontains", "name": "last name (partial string match)"},
        {"id": "first_name", "name": "given name"},
        {"id": "first_name__icontains", "name": "given name (partial match)"},
        {"id": "profession__name__icontains", "name": "profession/occupation (partial string match)"},
        {"id": "profession__name", "name": "profession/occupation (exact string match)"},
        {"id": "entid", "name": "ID"},
        {"id": "uri", "name": "URIS"}
    ]
    return data


def get_service_mainfest(request, base_uri=APIS_BASE_URI, project_name=PROJECT_NAME):
    domain = request.build_absolute_uri("/")
    schema_uri = f"{base_uri}schema/"
    entity_uri = f"{base_uri}entity/"
    openrefine_uri = f"{domain}apis/openrefine/"
    data = {
        "versions": ["0.1", "0.2"],
        "name": f"{project_name}",
        "identifierSpace": entity_uri,
        "schemaSpace": schema_uri,
        "defaultTypes": [
            {"id": f"{schema_uri}person", "name": "person"},
        ],
        "view": {
            "url": f"{domain}entity/" + "{{id}}/",
        },
        "preview": {
            "url": f"{domain}entity/" + "{{id}}/",
            "width": 600,
            "height": 400,
        },
        "batchSize": 50,
        "suggest": {"type": {"service_url": f"{openrefine_uri}suggest", "service_path": "/type"}},
        "extend": {
            "propose_properties": {"service_url": f"{openrefine_uri}properties", "service_path": ""},
            "property_settings": [
                {
                    "name": "entid",
                    "label": "entity id",
                    "type": "text",
                    "help_text": "entity id"
                }
            ],
        },
    }
    return data
