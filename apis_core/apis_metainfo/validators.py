#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
from django.core import validators
from django.core.validators import RegexValidator

# TODO __sresch__ old regex dict, remove once sure
# valid_date_regex_dict = {
#     "y": r"^\s*\d{3,4}\s*$",
#     "my": r"^\s*\d{1,2}(\.|-|\/)\d{3,4}\s*$",
#     "dmy": r"^\s*\d{1,2}(\.|-|\/)\d{1,2}(\.|-|\/)\d{3,4}\s*$",
#     "ym": r"^\s*\d{3,4}(\.|-|\/)\d{1,2}\.?\s*$",
#     "ymd": r"^\s*\d{3,4}(\.|-|\/)\d{1,2}(\.|-|\/)\d{1,2}\s*$",
#     "angle_brackets": r"^.*<(,,)?>|.*<\d{4}-\d{2}-\d{2}((, *(\d{4}-\d{2}-\d{2})?){2})?>$",
#     "y_ab_bis": r"^(( *\d{3,4} *)|( *ab? *\d{3,4} *(bis? *\d{3,4} *)?)|( *bis? *\d{3,4} *(ab? *\d{3,4} *)?))$",
#     "my_ab_bis": r"^(( *\d{1,2}(\.|-|\/)\d{3,4} *)|( *ab *\d{1,2}(\.|-|\/)\d{3,4} *(bis *\d{1,2}(\.|-|\/)\d{3,4} *)?)|( *bis *\d{1,2}(\.|-|\/)\d{3,4} *(ab *\d{1,2}(\.|-|\/)\d{3,4} *)?))$",
#     "dmy_ab_bis": r"^(( *\d{1,2}(\.|-|\/)\d{1,2}(\.|-|\/)\d{3,4} *)|( *ab *\d{1,2}(\.|-|\/)\d{1,2}(\.|-|\/)\d{3,4} *(bis *\d{1,2}(\.|-|\/)\d{1,2}(\.|-|\/)\d{3,4} *)?)|( *bis *\d{1,2}(\.|-|\/)\d{1,2}(\.|-|\/)\d{3,4} *(ab *\d{1,2}(\.|-|\/)\d{1,2}(\.|-|\/)\d{3,4} *)?))$",
#     "ym_ab_bis": r"^(( *\d{3,4}(\.|-|\/)\d{1,2} *)|( *ab *\d{3,4}(\.|-|\/)\d{1,2} *(bis *\d{3,4}(\.|-|\/)\d{1,2} *)?)|( *bis *\d{3,4}(\.|-|\/)\d{1,2} *(ab *\d{3,4}(\.|-|\/)\d{1,2} *)?))$",
#     "ymd_ab_bis": r"^(( *\d{3,4}(\.|-|\/)\d{1,2}(\.|-|\/)\d{1,2} *)|( *ab *\d{3,4}(\.|-|\/)\d{1,2}(\.|-|\/)\d{1,2} *(bis *\d{3,4}(\.|-|\/)\d{1,2}(\.|-|\/)\d{1,2} *)?)|( *bis *\d{3,4}(\.|-|\/)\d{1,2}(\.|-|\/)\d{1,2} *(ab *\d{3,4}(\.|-|\/)\d{1,2}(\.|-|\/)\d{1,2} *)?))$",
# }

# TODO __sresch__ remove once sure
# old:
# date_validator = RegexValidator(regex=re.compile(r'^.*$'),
# 	message="Please enter a valide date: (DD).(MM).YYYY",
# 	code='invalide_date')

# date_validator2 = RegexValidator(regex=re.compile(r'^([0-9]{1,2}\.[0-9]{1,2}\.)?[0-9]{4}$'),
# 	message="Please enter a valide date: (DD)-(MM)-YYYY.",
# 	code='invalide_date') still needed?



