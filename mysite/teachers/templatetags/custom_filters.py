from django import template
from django.utils.translation import gettext as _
from django.utils.formats import date_format
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def localized_datetime(value):
    if not value:
        return value

    hour = value.hour
    ampm = _("am_label") if hour < 12 else _("pm_label")

    formatted_date = date_format(value, "j F Y, H:i")

    return mark_safe(f"{formatted_date}&nbsp;{ampm}")