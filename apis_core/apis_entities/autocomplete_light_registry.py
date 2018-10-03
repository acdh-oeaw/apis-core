from autocomplete_light import shortcuts as al
from apis_core.vocabularies.models import ProfessionType, Title

from .models import Person, Place, Institution, Event, Work

class TitleAutocomplete(al.AutocompleteModelBase):
	search_fields=['name', 'abbreviation']
	model = Title
	attrs = {
        'data-autocomplete-minimum-characters': 2,
        'placeholder': 'Start typing to get suggestions',
    }

al.register(Title, TitleAutocomplete)


class ProfessionTypeAutocomplete(al.AutocompleteModelBase):
	search_fields=['name']
	model = ProfessionType
	attrs = {
        'data-autocomplete-minimum-characters': 2,
        'placeholder': 'Start typing to get suggestions',
    }

al.register(ProfessionType, ProfessionTypeAutocomplete)


class DB_PersonAutocomplete(al.AutocompleteModelBase):
    search_fields = ['name', 'first_name']
    model = Person
    attrs = {
        'data-autocomplete-minimum-characters': 2,
        'placeholder': 'Start typing to get suggestions',
    }

al.register(DB_PersonAutocomplete)


class DB_PlaceAutocomplete(al.AutocompleteModelBase):
    search_fields = ['name', ]
    model = Place
    attrs = {
        'data-autocomplete-minimum-characters': 2,
        'placeholder': 'Start typing to get suggestions',
    }

al.register(DB_PlaceAutocomplete)


class DB_InstitutionAutocomplete(al.AutocompleteModelBase):
    search_fields = ['name', ]
    model = Institution
    attrs = {
        'data-autocomplete-minimum-characters': 2,
        'placeholder': 'Start typing to get suggestions',
    }

al.register(DB_InstitutionAutocomplete)


class DB_EventAutocomplete(al.AutocompleteModelBase):
    search_fields = ['name', ]
    model = Event
    attrs = {
        'data-autocomplete-minimum-characters': 2,
        'placeholder': 'Start typing to get suggestions',
    }

al.register(DB_EventAutocomplete)


class DB_WorkAutocomplete(al.AutocompleteModelBase):
    search_fields = ['name', ]
    model = Work
    attrs = {
        'data-autocomplete-minimum-characters': 2,
        'placeholder': 'Start typing to get suggestions',
    }

al.register(DB_WorkAutocomplete)
