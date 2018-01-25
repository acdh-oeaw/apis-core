from django.db import models
from django.contrib.auth.models import User
from gm2m import GM2MField
#from reversion import revisions as reversion
import reversion
from django.contrib.contenttypes.models import ContentType
import re

from vocabularies.models import VocabNames
#from metainfo.models import Text


##############################################
#
#   Project classes
#
##############################################


class Project(models.Model):
    """Holds information on registered project.
    Id is used by the JavaScript function to target the right endpoints
    """
    name = models.CharField(max_length=255)  # name of the project registered
    user = models.ForeignKey(User)  # foreignkey to the User who created the project
    description = models.TextField(blank=True, null=True)
    base_url = models.URLField(blank=True, null=True)    # optional base URL to restrict highlights to a base URL
    store_text = models.BooleanField(default=False) # Whether to store the text in the tool or work with ids only.

    def __str__(self):
        return self.name


class TextHigh(models.Model):
    """ Holds unstructured text associated with
    one ore many entities/relations.
    """
    title = models.CharField(max_length=255, blank=True, null=True)
    text_choices = (('ft', 'Full Text'), ('id', 'Text ID'), ('cl', 'Text Class'))
    text_type = models.CharField(max_length=3, choices=text_choices, default='cl')
    uri = models.URLField(blank=True, null=True) # uri of vocab used to identify the text type
    text = models.TextField(blank=True, null=True)
    text_id = models.PositiveIntegerField(blank=True, null=True) # UID to identify the text within the project. Allows to not upload the texts.
    text_class = models.CharField(max_length=255, blank=True, null=True)
    project = models.ForeignKey(Project, blank=True, null=True)

    def __str__(self):
        return self.title


class AnnotationProject(models.Model):
    '''Every Project can have several Annotation Projects. Annotation Projects are used to track the precission etc.
    of automatic annotation tools.
    '''
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


@reversion.register()
class Annotation(models.Model):
    """Class storing highlights in full-texts
    """
    status_choices = (('del', 'deleted'), ('ap', 'approved'))
    start = models.PositiveIntegerField()   # number of string to start highlight
    end = models.PositiveIntegerField()     # number of string to end highlight
    entity_link = GM2MField(
        'entities.Person',
        'entities.Institution',
        'entities.Place',
        'entities.Event',
        'entities.Work',
        'entities.Coin',
        'entities.Artifact',
        'relations.PersonPerson',
        'relations.PersonPlace',
        'relations.PersonInstitution',
        'relations.PersonEvent',
        'relations.PersonWork',
        'relations.PersonCoin',
        'relations.PersonArtifact',
        'relations.InstitutionPlace',
        'relations.InstitutionEvent',
        'relations.InstitutionWork',
        'relations.InstitutionInstitution',
        'relations.InstitutionCoin',
        'relations.InstitutionArtifact',
        'relations.PlaceEvent',
        'relations.PlaceWork',
        'relations.PlacePlace',
        'relations.PlaceCoin',
        'relations.Placeartifact',
        'relations.EventWork',
        'relations.EventEvent',
        'relations.WorkWork',
        'relations.WorkCoin',
        'relations.WorkArtifact'
    )  # generic field to store the relation object
    entity_candidate = models.ManyToManyField('metainfo.UriCandidate', blank=True)
    orig_string = models.CharField(max_length=255, blank=True, null=True)    # string originally highlighted
    text = models.ForeignKey('metainfo.Text')
    parent = models.ForeignKey('self', related_name='parent_annotation', blank=True, null=True)    #parent annotations are used to allow for a stacked design of the annotation project
    user_added = models.ForeignKey(User, blank=True, null=True) #changed from default=12
    annotation_project = models.ForeignKey(AnnotationProject, blank=True, null=True)
    status = models.CharField(max_length=4, choices=status_choices, blank=True, null=True)

    def __str__(self):
        return "{}".format(self.pk)

    def trim_whitespaces(self, char):
        test = True
        while test and char < self.text_length:
            if self.text.text[char] == ' ':
                test = True
                char += 1
            else:
                return char

    def annotation_hash(self, format_string='start_end_text_ent_entid'):
        """
        Function that returns a hash of the annotaion used to calculate inter-annotator agreement.

        :return:
        """
        matching = {'start': 'start', 'end': 'end', 'text': 'text_id'}
        f_list = format_string.split('_')
        if 'start' not in f_list or 'end' not in f_list or 'text' not in f_list:
            raise AttributeError('Start, end and text must be present in the format_string parameter')
        res = ''
        self.text_length = len(self.text.text)
        self.start = self.trim_whitespaces(self.start)
        self.end = self.trim_whitespaces(self.end)
        for f in f_list:
            if f in matching.keys():
                res += str(getattr(self, matching[f]))
            else:
                ent_link = self.entity_link.all()
                if len(ent_link) > 0:
                    cont_lst = str(ContentType.objects.get_for_model(ent_link[0])).split()
                    if f == 'ent':
                        res += ''.join(cont_lst)
                    elif f == 'entid':
                        for cont in cont_lst:
                            if hasattr(ent_link[0], 'related_'+cont.strip()):
                                res += str(getattr(ent_link[0], 'related_'+cont.strip()+'_id'))
                            elif hasattr(ent_link[0], 'related_'+cont.strip()+'A'):
                                res += str(getattr(ent_link[0], 'related_'+cont.strip()+'A_id'))
                            elif hasattr(ent_link[0], 'related_'+cont.strip()+'B'):
                                res += str(getattr(ent_link[0], 'related_'+cont.strip()+'B_id'))
                            res += '-'
                        res = res[:-1]
                    elif f == 'rel':
                        res += str(getattr(ent_link[0], 'relation_type_id'))
                else:
                    res += 'NONE'
            res += '_'
        return res[:-1]

    def get_html_markup(self):
        if not len(self.entity_link.all()) == 1:
            return None
        rel_entity = self.entity_link.all()[0]
        if hasattr(rel_entity, 'relation_type'):
            entity_kind = str(rel_entity.relation_type.pk)
        elif hasattr(rel_entity, 'kind'):
            entity_kind = str(rel_entity.kind.pk)
        entity_type = type(rel_entity).__name__
        entity_type_app = ContentType.objects.get(model=entity_type).app_label
        ent_lst_pk = []
        user_added = self.user_added.username[:2]
        if entity_type_app.lower() == 'relations':
            for x in dir(rel_entity):
                c = re.match('related_\w+_id', x)
                if c:
                    ent_lst_pk.append(str(getattr(rel_entity, c.group(0))))
        start_span = '''<mark class="highlight hl_text_{}" data-hl-type="simple" data-hl-start="{}"
            data-hl-end="{}" data-hl-text-id="{}" data-hl-ann-id="{}" data-entity-class="{}" data-entity-pk="{}"
            data-related-entity-pk="{}" data-entity-type="{}" data-user-added={}>'''.format(entity_kind, self.start, self.end,
                                                                        self.text_id, self.pk, entity_type, rel_entity.pk,
                                                                                 ','.join(ent_lst_pk),
                                                                                 entity_type_app, user_added)
        return start_span

##############################################
#
#   Configuration Classes
#
##############################################

class VocabularyAPI(models.Model):
    """Class storing the information of the endpoints of the vocabularies.
    """
    method_lst = (('l','local'), ('o', 'open skos'))
    name = models.CharField(max_length=255, null=True, blank=True)
    api_endpoint = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(max_length=2, choices=method_lst, default='l')

    def __str__(self):
        return self.name


class MenuEntry(models.Model):
    """Class that defines the menu structure of the context menu
    """
    choices_kind = (('txt', 'Text field'), ('frm', 'Form'), ('m', 'menu entry'), ('fn', 'Javascript function'))
    kind = models.CharField(max_length=4, choices=choices_kind, default='txt')
    name = models.CharField(max_length=255, null=True, blank=True)    # Charfield used when txt is as type of entry specified
    api = models.ForeignKey(VocabularyAPI, blank=True, null=True)  # Foreignkey used to link the API entry in case api is set as kind
    parent = models.ForeignKey('self', related_name='parent_menuEntry', blank=True, null=True)
    project = models.ForeignKey(Project, null=True, blank=True)

    def __str__(self):
        return self.name
