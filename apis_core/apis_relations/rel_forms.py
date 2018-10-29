from crispy_forms.helper import FormHelper


class PersonPlaceFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(PersonPlaceFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = 'genericFilterForm'
        self.form_method = 'GET'
        self.helper.form_tag = False
        self.add_input(Submit('Filter', 'Search'))
        self.layout = Layout(
            Fieldset(
                'Basic search options',
                'related_person',
                'related_place',
                css_id="basic_search_fields"
                ),
            Accordion(
                AccordionGroup(
                    'Advanced search',
                    'relation_type',
                    css_id="more"
                    ),
                )
            )
