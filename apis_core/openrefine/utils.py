from django.conf import settings

APIS_BASE_URI = settings.APIS_BASE_URI
PROJECT_NAME = settings.PROJECT_NAME


def get_properties():
    data = [
        {"id": "entid", "name": "ID"},
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
            {"id": f"{schema_uri}place", "name": "place"},
            {"id": f"{schema_uri}institution", "name": "institution"},
            {"id": f"{schema_uri}event", "name": "event"},
            {"id": f"{schema_uri}work", "name": "work"},
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
