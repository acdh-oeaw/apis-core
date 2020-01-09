import re
import unicodedata
import math
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from dateutil.parser import parse
import requests

# from reversion import revisions as reversion
import reversion
from apis_core.apis_entities.serializers_generic import EntitySerializer
from apis_core.apis_labels.models import Label
from apis_core.apis_vocabularies.models import CollectionType, LabelType, TextType

# from helper_functions.highlighter import highlight_text
from apis_core.default_settings.NER_settings import autocomp_settings
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.urls import NoReverseMatch, reverse
from django.utils.functional import cached_property
from model_utils.managers import InheritanceManager

NEXT_PREV = getattr(settings, "APIS_NEXT_PREV", True)


if "apis_highlighter" in settings.INSTALLED_APPS:
    from apis_highlighter.models import Annotation


@reversion.register()
class TempEntityClass(models.Model):
    """ Base class to bind common attributes to many classes.

    The common attributes are:
    written start and enddates
    recognized start and enddates which are derived by RegEx
    from the written dates.
    A review boolean field to mark an object as reviewed
    """

    name = models.CharField(max_length=255, blank=True)
    review = models.BooleanField(
        default=False,
        help_text="Should be set to True, if the data record holds up quality standards.",
    )
    start_date = models.DateField(blank=True, null=True)
    start_start_date = models.DateField(blank=True, null=True)
    start_end_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_start_date = models.DateField(blank=True, null=True)
    end_end_date = models.DateField(blank=True, null=True)
    start_date_written = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Start",
    )
    end_date_written = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="End",
    )
    text = models.ManyToManyField("Text", blank=True)
    collection = models.ManyToManyField("Collection")
    status = models.CharField(max_length=100)
    source = models.ForeignKey(
        "Source", blank=True, null=True, on_delete=models.SET_NULL
    )
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    objects = models.Manager()
    objects_inheritance = InheritanceManager()


    def __str__(self):
        if self.name != "" and hasattr(
            self, "first_name"
        ):  # relation usually don´t have names
            return "{}, {} (ID: {})".format(self.name, self.first_name, self.id)
        elif self.name != "":
            return "{} (ID: {})".format(self.name, self.id)
        else:
            return "(ID: {})".format(self.id)

    def save(self, parse_dates=True, *args, **kwargs):
        """Adaption of the save() method of the class to automatically parse string-dates into date objects
        """


        def parse_dates_func(temp_entity_class):
            """
            function to parse the two date fields (start_date, end_date) of a TempEntityClass instance

            :param temp_entity_class: TempEntityClass
                the instance which fields' should be parsed from
                and into which depending sub fields the parsed sub dates and ranges should be written to
            """


            def parse_date_individual(date_string):
                """
                function to parse a string date field of an entity

                :param date_string : str :
                    the field value passed by a user

                :return date_single : datetime :
                    single date which represents either the precise date given by user or median in between a range.

                :return date_ab : datetime :
                    starting date of a range if user passed a range value either implicit or explicit.

                :return date_bis : datetime :
                    ending date of a range if user passed a range value either implicit or explicit.
                """


                def parse_date_range_individual(date, ab=False, bis=False):
                    """
                    As a sub function to parse_date, this function parse_date_individual handles a very single date since
                    in a text field a user can pass multiple dates.


                    :param date : str :
                        recognized sub string which potentially is a date (in julian calendar format)

                    :param ab : boolean : optional
                        indicates if a single date shall be intepreted as a starting date of a range

                    :param bis : boolean : optional
                        indicates if a single date shall be intepreted as an ending date of a range


                    :return tuple (datetime, datetime) :
                        two datetime objects representing the dates.
                        Two indicate that an implicit single date range was given (e.g. a year without months or days).
                        Has to be further processed then since it can be either a starting or ending date range.
                    or
                    :return datetime :
                        One datetime object representing the date.
                        if a single date was given.
                    """


                    def get_last_day_of_month(month, year):
                        """
                        Helper function to return the last day of a given month and year (respecting leap years)

                        :param month : int

                        :param year : int

                        :return day : int
                        """

                        if month in [1, 3, 5, 7, 8, 10, 12]:
                            # 31 day months
                            return 31
                        elif month in [4, 6, 9, 11]:
                            # 30 day months
                            return 30
                        elif month == 2:
                            # special case february, differentiate leap years with respect to gregorian leap rules
                            if year % 4 == 0:
                                if year % 100 == 0:
                                    if year % 400 == 0:
                                        # divisible by 4, by 100, by 400
                                        # thus is leap year
                                        return 29
                                    else:
                                        # divisible by 4, by 100, not by 400
                                        # thus is not leap yar
                                        return 28
                                else:
                                    # divisible by 4, not by 100, if by 400 doesn't matter
                                    # thus is leap year
                                    return 29
                            else:
                                # not divisible by 4, if by 100 or by 400 doesn't matter
                                return 28
                        else:
                            # no valid month
                            raise ValueError("Month " + str(month) + " does not exist.")



                    # replace all kinds of delimiters
                    date = date.replace(" ", "").replace("-", ".").replace("/", ".").replace("\\", ".")

                    # parse into variables for use later
                    year = None
                    month = None
                    day = None

                    # check for all kind of Y-M-D combinations
                    if re.match(r"\d{3,4}$", date):
                        # year
                        year = int(date)

                    elif re.match(r"\d{1,2}\.\d{3,4}$", date):
                        # month - year
                        tmp = re.split(r"\.", date)
                        month = int(tmp[0])
                        year = int(tmp[1])

                    elif re.match(r"\d{1,2}\.\d{1,2}\.\d{3,4}$", date):
                        # day - month - year
                        tmp = re.split(r"\.", date)
                        day = int(tmp[0])
                        month = int(tmp[1])
                        year = int(tmp[2])

                    elif re.match(r"\d{3,4}\.\d{1,2}\.?$", date):
                        # year - month
                        tmp = re.split(r"\.", date)
                        year = int(tmp[0])
                        month = int(tmp[1])

                    elif re.match(r"\d{3,4}\.\d{1,2}\.\d{1,2}\.?$", date):
                        # year - month - day
                        tmp = re.split(r"\.", date)
                        year = int(tmp[0])
                        month = int(tmp[1])
                        day = int(tmp[2])
                    else:
                        # No sensical interpretation found
                        raise ValueError("Could not interpret date.")


                    if (ab and bis) or year is None:
                        # both ab and bis in one single date are not valid, neither is the absence of a year.
                        raise ValueError("Could not interpret date.")

                    elif not ab and not bis and (month is None or day is None):
                        # if both ab and bis are False and either month or day is empty, then it was given
                        # an implicit date range (range of all months if given a year or all days if given a month)

                        # construct implicit month range
                        if month is None:
                            month_ab = 1
                            month_bis = 12
                        else:
                            month_ab = month
                            month_bis = month

                        # construct implicit day range
                        if day is None:
                            day_ab = 1
                            day_bis = get_last_day_of_month(month_bis, year)
                        else:
                            day_ab = day
                            day_bis = day


                        # return a tuple from a single date (which the calling function has to further process)
                        return (
                            datetime(year=year, month=month_ab, day=day_ab),
                            datetime(year=year, month=month_bis, day=day_bis)
                        )

                    else:
                        # Either ab or bis is True. Then use the respective beginning or end of range and construct a precise date
                        # Or both ab and bis are False. Then construct a precise date from parsed values

                        # construct implicit month range if month is None
                        if month is None:
                            if ab and not bis:
                                # is a starting date, thus take first month of year
                                month = 1
                            elif not ab and bis:
                                # is an ending date, thus take last month of year
                                month = 12

                        # construct implicit day range if day is None
                        if day is None:
                            if ab and not bis:
                                # is a starting date, thus take first day of month
                                day = 1
                            elif not ab and bis:
                                # is an ending date, thus take last month of year
                                day = get_last_day_of_month(month=month, year=year)

                        return datetime(year=year, month=month, day=day)


                # return variables
                date_single = None
                date_ab = None
                date_bis = None

                # split for angle brackets, check if explicit iso date is contained within them
                date_split_angle = re.split(r"(<.*?>)", date_string)

                if len(date_split_angle) > 1:
                    # date string contains angle brackets. Parse them, ignore the rest

                    def parse_iso_date(date_string):
                        date_string_split = date_string.split("-")
                        try:
                            return datetime(year=int(date_string_split[0]), month=int(date_string_split[1]), day=int(date_string_split[2]) )
                        except:
                            raise ValueError("Invalid iso date: ", date_string)

                    if len(date_split_angle) > 3:
                        # invalid case
                        raise ValueError("Too many angle brackets.")

                    elif len(date_split_angle) == 3:
                        # the right amount of substrings, indicating exactly one pair of angle brackets.
                        # Parse the iso date in between

                        # remove angle brackets and split by commas
                        dates_iso = date_split_angle[1][1:-1]

                        # check for commas, which would indicate that either one iso date or three are being input
                        dates_iso = dates_iso.split(",")
                        if len(dates_iso) != 1 and len(dates_iso) != 3:
                            # only either one iso date or three are allowed
                            raise ValueError(
                                "Incorrect number of dates given. Within angle brackets only one or three (separated by commas) are allowed.")

                        elif len(dates_iso) == 3:
                            # three iso dates indicate further start and end dates

                            # parse start date
                            date_ab_string = dates_iso[1].strip()
                            if date_ab_string != "":
                                date_ab = parse_iso_date(date_ab_string)

                            # parse end date
                            date_bis_string = dates_iso[2].strip()
                            if date_bis_string != "":
                                date_bis = parse_iso_date(date_bis_string)

                        # parse single date
                        date_single_string = dates_iso[0].strip()
                        if date_single_string != "":
                            date_single = parse_iso_date(date_single_string)


                else:
                    # date string contains no angle brackets. Interpret the possible date formats
                    date_string = date_string.lower()
                    date_string = date_string.replace(" ","")

                    # helper variables for the following loop
                    found_ab = False
                    found_bis = False
                    found_single = False

                    # split by allowed keywords 'ab' and 'bis' and iterate over them
                    date_split_ab_bis = re.split(r"(ab|bis)", date_string)
                    for i, v in enumerate(date_split_ab_bis):

                        if v == "ab":
                            # indicates that the next value must be a start date

                            if found_ab or found_single:
                                # if already found a ab_date or single date before then there is non-conformative redundancy
                                raise ValueError("Redundant dates found.")
                            found_ab = True

                            # parse the next value which must be a parsable date string
                            date_ab = parse_date_range_individual(date_split_ab_bis[i + 1], ab=True)

                        elif v == "bis":
                            # indicates that the next value must be an end date

                            if found_bis or found_single:
                                # if already found a bis_date or single date before then there is non-conformative redundancy
                                raise ValueError("Redundant dates found.")
                            found_bis = True

                            # parse the next value which must be a parsable date string
                            date_bis = parse_date_range_individual(date_split_ab_bis[i + 1], bis=True)

                        elif v != "" and not found_ab and not found_bis and not found_single:
                            # indicates that this value must be a date

                            found_single = True

                            # parse the this value which must be a parsable date string
                            date_single = parse_date_range_individual(v)

                            if type(date_single) is tuple:
                                #  if result of parse_date_range_individual is a tuple then the date was an implict range.
                                #  Then split it into start and end dates
                                date_ab = date_single[0]
                                date_bis = date_single[1]

                    if date_ab and date_bis:
                        # date is a range

                        if date_ab > date_bis:
                            raise ValueError("'ab-date' must be before 'bis-date' in time")

                        # calculate difference between start and end date of range,
                        # and use it to calculate a single date for usage as median.
                        days_delta_half = math.floor((date_bis - date_ab).days / 2, )
                        date_single = date_ab + timedelta(days=days_delta_half)

                    elif date_ab is not None and date_bis is None:
                        # date is only the start of a range, save it also as the single date

                        date_single = date_ab

                    elif date_ab is None and date_bis is not None:
                        # date is only the end of a range, save it also as the single date

                        date_single = date_bis

                return date_single, date_ab, date_bis

            # overwrite every field with None as default
            start_date = None
            start_start_date = None
            start_end_date = None
            end_date = None
            end_start_date = None
            end_end_date = None


            if temp_entity_class.start_date_written:
                # If some textual user input of a start date is there, then parse it

                try:
                    start_date, start_start_date, start_end_date = \
                        parse_date_individual(temp_entity_class.start_date_written)
                except Exception as e:
                    print("Could not parse date: ", temp_entity_class.start_date_written, "ERROR:", e)

            if temp_entity_class.end_date_written:
                # If some textual user input of an end date is there, then parse it

                try:
                    end_date, end_start_date, end_end_date = \
                        parse_date_individual(temp_entity_class.end_date_written)
                except Exception as e:
                    print("Could not parse date: ", temp_entity_class.end_date_written, "ERROR:", e)


            temp_entity_class.start_date = start_date
            temp_entity_class.start_start_date = start_start_date
            temp_entity_class.start_end_date = start_end_date
            temp_entity_class.end_date = end_date
            temp_entity_class.end_start_date = end_start_date
            temp_entity_class.end_end_date = end_end_date

        if parse_dates:
            parse_dates_func(self)

        if self.name:
            self.name = unicodedata.normalize("NFC", self.name)

        super(TempEntityClass, self).save(*args, **kwargs)

        return self

    def get_child_entity(self):
        for x in [x for x in apps.all_models['apis_entities'].values()]:
            if x.__name__ in list(settings.APIS_ENTITIES.keys()):
                try:
                    my_ent = x.objects.get(id=self.id)
                    return my_ent
                    break
                except ObjectDoesNotExist:
                    pass
        return None

    @classmethod
    def get_listview_url(self):
        entity = self.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_list",
                kwargs={"entity": entity},
            )
        else:
            return reverse(
                "apis_core:apis_relations:generic_relations_list",
                kwargs={"entity": entity},
            )

    @classmethod
    def get_createview_url(self):
        entity = self.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_create_view",
                kwargs={"entity": entity},
            )
        else:
            return None

    def get_edit_url(self):
        entity = self.__class__.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_edit_view",
                kwargs={"entity": entity, "pk": self.id},
            )
        else:
            return None

    def get_child_class(self):
        child = self.get_child_entity()
        if child:
            return "{}".format(child.__class__.__name__)
        else:
            return "{}".format(child.__class__.__name__)

    def get_absolute_url(self):
        entity = self.__class__.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_detail_view",
                kwargs={"entity": entity, "pk": self.id},
            )
        elif entity == "tempentityclass":
            return self.get_child_entity().get_absolute_url()
        else:
            return reverse(
                "apis_core:apis_relations:generic_relations_detail_view",
                kwargs={"entity": entity, "pk": self.id},
            )

    def get_prev_url(self):
        entity = self.__class__.__name__.lower()
        if NEXT_PREV:
            prev = self.__class__.objects.filter(id__lt=self.id).order_by("-id")
        else:
            return False
        if prev:
            if entity == "institution" or len(entity) < 10:
                return reverse(
                    "apis_core:apis_entities:generic_entities_detail_view",
                    kwargs={"entity": entity, "pk": prev.first().id},
                )
            else:
                return reverse(
                    "apis_core:apis_relations:generic_relations_detail_view",
                    kwargs={"entity": entity, "pk": prev.first().id},
                )
        else:
            return False

    def get_next_url(self):
        entity = self.__class__.__name__.lower()
        if NEXT_PREV:
            next = self.__class__.objects.filter(id__gt=self.id)
        else:
            return False
        if next:
            if entity == "institution" or len(entity) < 10:
                return reverse(
                    "apis_core:apis_entities:generic_entities_detail_view",
                    kwargs={"entity": entity, "pk": next.first().id},
                )
            else:
                return reverse(
                    "apis_core:apis_relations:generic_relations_detail_view",
                    kwargs={"entity": entity, "pk": next.first().id},
                )
        else:
            return False

    def get_delete_url(self):
        entity = self.__class__.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_delete_view",
                kwargs={"entity": entity, "pk": self.id},
            )
        else:
            return None

    def merge_with(self, entities):
        e_a = type(self).__name__
        self_model_class = ContentType.objects.get(
            app_label="apis_entities", model__iexact=e_a
        ).model_class()
        if isinstance(entities, int):
            entities = self_model_class.objects.get(pk=entities)
        if not isinstance(entities, list) and not isinstance(entities, QuerySet):
            entities = [entities]
            entities = [
                self_model_class.objects.get(pk=ent) if type(ent) == int else ent
                for ent in entities
            ]
        rels = ContentType.objects.filter(
            app_label="apis_relations", model__icontains=e_a
        )
        for ent in entities:
            e_b = type(ent).__name__
            if e_a != e_b:
                continue
            lt, created = LabelType.objects.get_or_create(name="Legacy name (merge)")
            col_list = list(self.collection.all())
            for col2 in ent.collection.all():
                if col2 not in col_list:
                    self.collection.add(col2)
            for f in ent._meta.local_many_to_many:
                if not f.name.endswith('_set'):
                    sl = list(getattr(self, f.name).all())
                    for s in getattr(ent, f.name).all():
                        if s not in sl:
                            getattr(self, f.name).add(s)
            Label.objects.create(label=str(ent), label_type=lt, temp_entity=self)
            for u in Uri.objects.filter(entity=ent):
                u.entity = self
                u.save()
            for l in Label.objects.filter(temp_entity=ent):
                l.temp_entity = self
                l.save()
            for r in rels.filter(model__icontains=e_b):
                lst_ents_rel = str(r).split()
                if lst_ents_rel[0] == lst_ents_rel[1]:
                    q_d = {"related_{}A".format(e_b.lower()): ent}
                    k = r.model_class().objects.filter(**q_d)
                    for t in k:
                        setattr(t, "related_{}A".format(e_a.lower()), self)
                        t.save()
                    q_d = {"related_{}B".format(e_b.lower()): ent}
                    k = r.model_class().objects.filter(**q_d)
                    for t in k:
                        setattr(t, "related_{}B".format(e_a.lower()), self)
                        t.save()
                else:
                    q_d = {"related_{}".format(e_b.lower()): ent}
                    k = r.model_class().objects.filter(**q_d)
                    for t in k:
                        setattr(t, "related_{}".format(e_a.lower()), self)
                        t.save()
            ent.delete()

    def get_serialization(self):
        return EntitySerializer(self).data


@reversion.register()
class Source(models.Model):
    """ Holds information about entities and their relations"""

    orig_filename = models.CharField(max_length=255, blank=True)
    indexed = models.BooleanField(default=False)
    pubinfo = models.CharField(max_length=400, blank=True)
    author = models.CharField(max_length=255, blank=True)
    orig_id = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        if self.author != "" and self.orig_filename != "":
            return "{}, stored by {}".format(self.orig_filename, self.author)
        else:
            return "(ID: {})".format(self.id)


@reversion.register()
class Collection(models.Model):
    """ Allows to group entities and relation. """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    collection_type = models.ForeignKey(
        CollectionType, blank=True, null=True, on_delete=models.SET_NULL
    )
    groups_allowed = models.ManyToManyField(Group)
    parent_class = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


@reversion.register()
class Text(models.Model):
    """ Holds unstructured text associeted with
    one ore many entities/relations. """

    kind = models.ForeignKey(TextType, blank=True, null=True, on_delete=models.SET_NULL)
    text = models.TextField(blank=True)
    source = models.ForeignKey(Source, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.text != "":
            return "ID: {} - {}".format(self.id, self.text[:25])
        else:
            return "ID: {}".format(self.id)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = Text.objects.get(pk=self.pk)
            if orig.text != self.text and "apis_highlighter" in settings.INSTALLED_APPS:
                ann = Annotation.objects.filter(text_id=self.pk).order_by("start")
                seq = SequenceMatcher(None, orig.text, self.text)
                for a in ann:
                    changed = False
                    count = 0
                    for s in seq.get_matching_blocks():
                        count += 1
                        if s.a <= a.start and (s.a + s.size) >= a.end:
                            a.start += s.b - s.a
                            a.end += s.b - s.a
                            a.save()
                            changed = True
                    if not changed:
                        a.delete()  # TODO: we might want to delete relations as well.
        super().save(*args, **kwargs)


@reversion.register()
class Uri(models.Model):
    uri = models.URLField(blank=True, null=True, unique=True, max_length=255)
    domain = models.CharField(max_length=255, blank=True)
    rdf_link = models.URLField(blank=True)
    entity = models.ForeignKey(
        TempEntityClass, blank=True, null=True, on_delete=models.CASCADE
    )
    # loaded set to True when RDF was loaded and parsed into the data model
    loaded = models.BooleanField(default=False)
    # Timestamp when file was loaded and parsed
    loaded_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.uri)

    def get_web_object(self):
        result = {
            "relation_pk": self.pk,
            "relation_type": "uri",
            "related_entity": self.entity.name,
            "related_entity_url": self.entity.get_absolute_url(),
            "related_entity_class_name": self.entity.__class__.__name__.lower(),
            "uri": self.uri,
        }
        return result

    @classmethod
    def get_listview_url(self):
        return reverse("apis_core:apis_metainfo:uri_browse")

    @classmethod
    def get_createview_url(self):
        return reverse('apis_core:apis_metainfo:uri_create')

    def get_absolute_url(self):
        return reverse('apis_core:apis_metainfo:uri_detail', kwargs={'pk': self.id})

    def get_delete_url(self):
        return reverse('apis_core:apis_metainfo:uri_delete', kwargs={'pk': self.id})

    def get_edit_url(self):
        return reverse('apis_core:apis_metainfo:uri_edit', kwargs={'pk': self.id})


@reversion.register()
class UriCandidate(models.Model):
    """Used to store the URI candidates for automatically generated entities.
    """

    uri = models.URLField()
    confidence = models.FloatField(blank=True, null=True)
    responsible = models.CharField(max_length=255)
    entity = models.ForeignKey(
        TempEntityClass, blank=True, null=True, on_delete=models.CASCADE
    )

    @cached_property
    def description(self):
        headers = {"accept": "application/json"}
        cn = TempEntityClass.objects_inheritance.get_subclass(
            id=self.entity_id
        ).__class__.__name__
        for endp in autocomp_settings[cn.title()]:
            url = re.sub(r"/[a-z]+$", "/entity", endp["url"])
            params = {"id": self.uri}
            res = requests.get(url, params=params, headers=headers)
            if res.status_code == 200:
                if endp["fields"]["descr"][0] in res.json()["representation"].keys():
                    desc = res.json()["representation"][endp["fields"]["descr"][0]][0][
                        "value"
                    ]
                else:
                    desc = "undefined"
                label = res.json()["representation"][endp["fields"]["name"][0]][0][
                    "value"
                ]
                return (label, desc)


#@receiver(post_save, sender=Uri, dispatch_uid="remove_default_uri")
#def remove_default_uri(sender, instance, **kwargs):
#    if Uri.objects.filter(entity=instance.entity).count() > 1:
#        Uri.objects.filter(entity=instance.entity, domain="apis default").delete()
