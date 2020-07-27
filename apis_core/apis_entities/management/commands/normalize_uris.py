import os

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from apis_core.apis_metainfo.models import Uri
from apis_core.helper_functions.RDFParser import clean_uri

uri_settings_file = os.path.join(
    settings.BASE_DIR, 'apis_core', 'default_settings', "URI_replace_settings.yml"
)

sett = yaml.load(open(uri_settings_file, 'r'))


class Command(BaseCommand):
    # Show this when the user types help
    help = "normalizes Uris"

    def handle(self, *args, **options):
        for x in Uri.objects.all():
            old_uri = x.uri
            new_uri = clean_uri(sett, old_uri)
            try:
                x.uri = new_uri
                x.save()
            except IntegrityError:
                print(x)
        return "all done"
