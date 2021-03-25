import dj_database_url

from .base import *
import sys


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

APIS_BASE_URI = "https://apis.acdh.oeaw.ac.at/"

ALLOWED_HOSTS = []

SECRET_KEY = (
    "d3j@454545()(/)@zlck/6dsaf*#sdfsaf*#sadflj/6dsfk-11$)d6ixcvjsdfsdf&-u35#ayi"
)
DEBUG = True
DEV_VERSION = False

TEST_RUNNER = "apis_core.testrunners.APISTestRunner"

# REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = (
#    "rest_framework.permissions.IsAuthenticatedOrReadOnly",
# )


INSTALLED_APPS = [
    "dal",
    # 'corsheaders',
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "reversion",
    # "reversion_compare",
    "crispy_forms",
    "django_filters",
    "django_tables2",
    "rest_framework",
    "browsing",
    "apis_core.apis_entities",
    "apis_core.apis_metainfo",
    "apis_core.apis_relations",
    "apis_core.apis_vocabularies",
    "apis_core.apis_labels",
    # 'apis_core.apis_vis',
    "rest_framework.authtoken",
    # "drf_yasg",
    "drf_spectacular",
    "guardian",
    "infos",
]

DATABASES = {}

DATABASES["default"] = dj_database_url.config(conn_max_age=600)

LANGUAGE_CODE = "de"
