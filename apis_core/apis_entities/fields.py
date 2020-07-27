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
        css = list(m._css['screen'])
        js_remove_list = ['admin/js/vendor/jquery/jquery.js',
                          'admin/js/vendor/jquery/jquery.min.js',
                          'autocomplete_light/jquery.post-setup.js',
                          'admin/js/vendor/select2/select2.full.js',
                          'admin/js/vendor/select2/select2.full.min.js',
                          'admin/js/vendor/select2/i18n/en.js'
                         ]
        css_remove_list = ['admin/css/vendor/select2/select2.css',
                           'admin/css/vendor/select2/select2.min.css',
                           'admin/css/autocomplete.css',
                          ]
        for e in js_remove_list:
            try:
                js.remove(e)
            except ValueError:
                pass
        for e in css_remove_list:
            try:
                css.remove(e)
            except ValueError:
                pass

        js.append('https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.5/js/select2.full.min.js')
        css.insert(0, 'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.5/css/select2.min.css')
        return forms.Media(css={'screen': css}, js=js)


class Select2(Select2WidgetMixin, DALSelect2):
    pass


class TagSelect2(Select2WidgetMixin, DALTagSelect2):
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
