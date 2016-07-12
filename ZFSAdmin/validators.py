from django.core.exceptions import ValidationError
import re
from django.utils.translation import ugettext_lazy as _


def validate_filesystem_value(value):
    if re.search(r"[^A-Za-z0-9-_/]", value):
        raise ValidationError(
            _('{} contained invalid characters'.format(value)),
        )


def validate_ips_value(value):
    if re.search(r"[^A-Za-z0-9-_/:.|]", value):
        raise ValidationError(
            _('{} contained invalid characters'.format(value)),
        )

def validate_username_value(value):
    if re.search(r"[^A-Za-z0-9]", value):
        raise ValidationError(
            _('{} contained invalid characters'.format(value)),
        )
