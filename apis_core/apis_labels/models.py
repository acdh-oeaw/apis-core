from django.db import models
from apis_core.apis_vocabularies.models import LabelType
#from metainfo.models import TempEntityClass
#from reversion import revisions as reversion
import reversion

import unicodedata


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
        super(Label, self).save(*args, **kwargs)
        return self
