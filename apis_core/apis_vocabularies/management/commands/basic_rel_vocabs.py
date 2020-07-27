from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    # Show this when the user types help
    help = "creates 'related' vocabs entries for all Relation classes"

    def handle(self, *args, **kwargs):
        for x in apps.get_app_config('apis_vocabularies').get_models():
            if x.__name__.endswith('Relation'):
                x.objects.get_or_create(
                    name="related",
                    name_reverse="related"
                )
