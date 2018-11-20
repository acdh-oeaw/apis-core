from dal.autocomplete import ListSelect2 as DALListSelect2
from dal.autocomplete import ModelSelect2 as DALModelSelect2
from dal.autocomplete import ModelSelect2Multiple as DALModelSelect2Multiple
from dal.autocomplete import Select2 as DALSelect2
from dal.autocomplete import Select2Multiple as DALSelect2Multiple
from dal.autocomplete import TagSelect2 as DALTagSelect2
from dal_select2.widgets import Select2WidgetMixin as DALSelect2WidgetMixin
from django import forms

# "Rewrite" select2 widgets from Django Autocomplete Light so
# that they don't use Django's admin-provided jQuery, which
# causes errors with jQuery provided by us.
class Select2WidgetMixin(DALSelect2WidgetMixin):
    @property
    def media(self):
        m = super().media
        js = list(m._js) 
        try:
            js.remove('admin/js/vendor/jquery/jquery.js')
            js.remove('autocomplete_light/jquery.post-setup.js')
            #js.remove('admin/js/vendor/jquery/jquery.min.js')
        except ValueError:
            print('Error')
            pass
        return forms.Media(css=m._css, js=js)


class Select2(Select2WidgetMixin, DALSelect2):
    pass


class Select2Multiple(Select2WidgetMixin, DALSelect2Multiple):
    pass


class ListSelect2(Select2WidgetMixin, DALListSelect2):
    pass


class ModelSelect2(Select2WidgetMixin, DALModelSelect2):
    pass


class ModelSelect2Multiple(Select2WidgetMixin, DALModelSelect2Multiple):
    pass


class TagSelect2(Select2WidgetMixin, DALTagSelect2):
    pass
