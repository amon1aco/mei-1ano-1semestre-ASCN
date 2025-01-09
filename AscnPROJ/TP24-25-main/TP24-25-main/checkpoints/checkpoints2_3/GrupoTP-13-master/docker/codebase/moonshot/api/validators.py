from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import re


def dosage_num_validator(value):
    exp = r"\d/\d"
    if re.match(exp, value) is None:
        raise ValidationError(_("Invalid dosage number! Example: 1/2"))
