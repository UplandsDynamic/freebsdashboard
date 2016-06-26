import django_tables2 as tables
from .models import ZfsSnapshot
from .templatetags import zfsadmin_extras


class SnapshotTable(tables.Table):
	# modify field names if for display
	dataset = tables.Column(verbose_name='ZFS File System Dataset')
	datetime_created = tables.Column(verbose_name='Created', localize=True)
	retention = tables.Column(verbose_name='Longevity (mins)')
	name = tables.Column(verbose_name='Delete', orderable=False)

	# Any custom renders of columns. Only needs specifying if custom tags/filters, etc.

	def render_name(self, value):
		return zfsadmin_extras.str_to_cbox_value(value)

	def render_retention(self, value):
		return zfsadmin_extras.zero_to_unset(value)

	class Meta:
		model = ZfsSnapshot
		# adds classes to <table> tag
		attrs = {"class": "table table-hover snapshot-table"}
		fields = ('dataset', 'datetime_created', 'retention', 'name')
