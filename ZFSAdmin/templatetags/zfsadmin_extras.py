from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape

register = template.Library()


@register.filter(needs_autoescape=True)
@stringfilter
def str_to_cbox_value(value, autoescape=True):
	if autoescape:
		esc = conditional_escape
	else:
		esc = lambda x: x
	checkboxes = 'Clone <input style="margin-right:2em;" class="clone_checkbox" type="checkbox" value="{}"></input>' \
	             'Delete <input class="delete_checkbox" type="checkbox" value="{}"></input>'.format(value, value)
	return mark_safe(checkboxes)


@register.filter(needs_autoescape=True)
@stringfilter
def zero_to_unset(value, autoescape=True):
	if autoescape:
		esc = conditional_escape
	else:
		esc = lambda x: x
	if value == '0':
		value = 'Unset'
	return mark_safe(value)
