from django.conf import settings


def default_strings(request):
	return {
		'default_footer_text': settings.DEFAULT_FOOTER_TEXT,
		'default_site_name': settings.DEFAULT_SITE_NAME,
	}