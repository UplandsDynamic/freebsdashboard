from django.contrib import admin
from ZFSAdmin.models import *

# # Register your models here.
admin.site.register(ZfsSnapshot)
admin.site.register(TaskManager)
admin.site.register(ZfsDatasets)