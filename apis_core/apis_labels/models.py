import unicodedata

# from metainfo.models import TempEntityClass
# from reversion import revisions as reversion
import reversion
from django.db import models

from apis_core.apis_vocabularies.models import LabelType
from apis_core.helper_functions import DateParser


@reversion.register()
class Label(models.Model):
    label = models.CharField(
        max_length=255, blank=True, help_text="The entities label or name.")
    isoCode_639_3 = models.CharField(
        max_length=3, blank=True, null=True,
        help_text="The ISO 639-3 (or 2) code for the label's language.",
        verbose_name='ISO Code', default='deu')
    label_type = models.ForeignKey(LabelType, blank=True, null=True,
                                   on_delete=models.SET_NULL)

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

    # TODO __sresch__ add related_name="label_set" here to be consistent with other usages throughout django
    temp_entity = models.ForeignKey("apis_metainfo.TempEntityClass", on_delete=models.CASCADE)

    def get_web_object(self):
        result = {
            'relation_pk': self.pk,
            'label': self.label,
            'isoCode_639_3': self.isoCode_639_3,
            'label_type': self.label_type.name}
        return result

    def save(self, *args, **kwargs):
        if self.label != unicodedata.normalize('NFC', self.label):    #secure correct unicode encoding
            self.label = unicodedata.normalize('NFC', self.label)

        def parse_dates():

            # overwrite every field with None as default
            start_date = None
            start_start_date = None
            start_end_date = None
            end_date = None
            end_start_date = None
            end_end_date = None

            if self.start_date_written:
                # If some textual user input of a start date is there, then parse it

                start_date, start_start_date, start_end_date = \
                    DateParser.parse_date(self.start_date_written)

            if self.end_date_written:
                # If some textual user input of an end date is there, then parse it

                end_date, end_start_date, end_end_date = \
                    DateParser.parse_date(self.end_date_written)

            self.start_date = start_date
            self.start_start_date = start_start_date
            self.start_end_date = start_end_date
            self.end_date = end_date
            self.end_start_date = end_start_date
            self.end_end_date = end_end_date

        parse_dates()

        super(Label, self).save(*args, **kwargs)
        return self

    def __str__(self):
        return self.label
