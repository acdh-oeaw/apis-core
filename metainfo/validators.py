#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
from django.core import validators
from django.core.validators import RegexValidator


date_validator = RegexValidator(regex=re.compile(r'^([0-9]{1,2}\.[0-9]{1,2}\.)?[0-9]{4}$'), 
	message="Please enter a valide date: (DD).(MM).YYYY",
	code='invalide_date')
# date_validator2 = RegexValidator(regex=re.compile(r'^([0-9]{1,2}\.[0-9]{1,2}\.)?[0-9]{4}$'),
# 	message="Please enter a valide date: (DD)-(MM)-YYYY.",
# 	code='invalide_date') still needed?