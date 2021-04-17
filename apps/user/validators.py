from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class PKUIDValidator(validators.RegexValidator):
    regex = r"^[0-9]{10}\Z"
    message = _("Enter a valid pku id. This value may contain only numbers.")
    flags = 0
