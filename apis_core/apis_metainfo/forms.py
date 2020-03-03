from django import forms
from dal import autocomplete
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit,  Layout, Fieldset, Div, MultiField, HTML
from crispy_forms.bootstrap import Accordion, AccordionGroup
from . models import *


class UriForm(forms.ModelForm):
    class Meta:
        model = Uri
        fields = "__all__"
        widgets = {
            'entity': autocomplete.ModelSelect2(
                url='apis_core:apis_metainfo-ac:apis_tempentity-autocomplete'),
            }

    def __init__(self, *args, **kwargs):
        super(UriForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        self.helper.add_input(Submit('submit', 'save'),)


class UriFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(UriFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = 'genericFilterForm'
        self.form_method = 'GET'
        self.helper.form_tag = False
        self.add_input(Submit('Filter', 'Search'))
        self.layout = Layout(
            Accordion(
                AccordionGroup(
                    'Filter',
                    'uri',
                    'domain',
                    'entity__name',
                    css_id="basic_search_fields"
                    ),
                )
            )



def get_date_help_text_default():

    return "Dates are interpreted by defined rules. If this fails, an iso-date can be explicitly set with '&lt;YYYY-MM-DD&gt;'."



def get_date_help_text_from_dates(single_date, single_start_date, single_end_date, single_date_written, single_date_is_exact):
    """
    function for creating string help text from parsed dates, to provide feedback to the user
    about the parsing status of a given date field.

    :param single_date: datetime :
        the individual date point

    :param single_start_date: datetime :
        the start range of a date

    :param single_end_date: datetime :
        the endrange of a date

    :param single_date_written: str :
        the textual user entry of a date field (needed to check if empty or not)

    :param single_date_is_exact: bool :
        if the given date is defined as to be exact or not

    :return help_text: str :
        The text to be displayed underneath a date field, informing the user about the parsing result
    """


    # check which of the dates could be parsed to construct the relevant feedback text

    help_text = ""
    if single_date:
        # single date could be parsed

        help_text = "Date interpreted as "

        if single_date_is_exact:
            help_text += "exactly: "
        else:
            help_text += "not exactly: "

        if single_start_date or single_end_date:
            # date has also start or end ranges, then ignore single date

            if single_start_date:
                # date has start range

                # convert gregorian database date format into julian for user layer
                single_start_date_j = julian.from_gregorian(
                    year=single_start_date.year,
                    month=single_start_date.month,
                    day=single_start_date.day
                )

                help_text += \
                    str(single_start_date_j[0]) + "-" + \
                    str(single_start_date_j[1]) + "-" + \
                    str(single_start_date_j[2]) + " until "

            else:
                # date has no start range, then write "undefined"

                help_text += "undefined start until "

            if single_end_date:
                # date has end range

                # convert gregorian database date format into julian for user layer
                single_end_date_j = julian.from_gregorian(
                    year=single_end_date.year,
                    month=single_end_date.month,
                    day=single_end_date.day
                )

                help_text += \
                    str(single_end_date_j[0]) + "-" + \
                    str(single_end_date_j[1]) + "-" + \
                    str(single_end_date_j[2])

            else:
                # date has no start range, then write "undefined"

                help_text += "undefined end"

        else:
            # date has no start nor end range. Use single date then.

            # convert gregorian database date format into julian for user layer
            single_date_j = julian.from_gregorian(
                year=single_date.year,
                month=single_date.month,
                day=single_date.day
            )

            help_text += \
                str(single_date_j[0]) + "-" + \
                str(single_date_j[1]) + "-" + \
                str(single_date_j[2])

    elif single_date_written is not None:
        # date input field is not empty but it could not be parsed either. Show parsing info and help text

        help_text = "<b>Date could not be interpreted</b><br>" + get_date_help_text_default()

    else:
        # date field is completely empty. Show help text only

        help_text = get_date_help_text_default()

    return help_text
