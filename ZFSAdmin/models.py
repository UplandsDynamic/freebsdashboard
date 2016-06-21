from django.db import models


class ZfsDatasets(models.Model):
	dataset_name = models.CharField(max_length=255)

	def __str__(self):
		return self.dataset_name


class ZfsSnapshot(models.Model):
	dataset = models.CharField(max_length=255, unique=False)
	datetime_created = models.DateTimeField(null=True, blank=True)
	retention = models.BigIntegerField(default=10080)
	name = models.CharField(max_length=255, null=False, default="unknown")

	class Meta:
		unique_together = ('datetime_created', 'dataset')

	def __str__(self):
		return self.dataset


class TaskManager(models.Model):
	task_id = models.CharField(max_length=255)
	datetime_created = models.DateTimeField(null=False, blank=False, auto_now=True)
	process_id = models.CharField(max_length=255, null=True)
	error_flag = models.BooleanField(default=False)
	error_detail = models.CharField(max_length=255, null=True)
	complete = models.BooleanField(default=False)

	def __str__(self):
		return self.task_id
