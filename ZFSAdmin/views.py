#!/usr/bin/env python3
import os
import sys
import logging
from django.conf import settings
from django.views import generic
from django.shortcuts import render
from django_tables2 import RequestConfig
from django_q.tasks import async
from django.http import JsonResponse
from django.shortcuts import redirect
from .models import TaskManager, ZfsSnapshot, ZfsDatasets
from .tables import SnapshotTable
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import ZFSAdmin.engineering as engineering
from .forms import DatasetSelection
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
logger = logging.getLogger(__name__)


class IndexView(LoginRequiredMixin, generic.View):
	template_name = 'ZFSAdmin/snapshot_table.html'

	def get(self, request):
		# define context dict for return
		context = {}
		# set timezone to UTC if not already set to something else
		if 'django_timezone' not in request.session:
			request.session['django_timezone'] = 'UTC'
		# Get snapshots_demo.txt
		snapshot_qset = ZfsSnapshot.objects.all()
		# get datasets for later reference
		datasets = snapshot_qset.values_list('dataset', flat=True).order_by('dataset')
		context['datasets'] = set(datasets)  # just add the unique datasets to context
		# filter results if necessary
		if request.GET.get('filter'):
			snapshot_qset = snapshot_qset.filter(
				dataset=request.GET.get('filter')).values()
		# if debug is true, restart uwsgi every reload to reflect code changes
		if settings.DEBUG:
			'''DEBUG - uncomment below to clear running task'''
		# TaskManager.objects.all().delete()
		if snapshot_qset:
			table = SnapshotTable(snapshot_qset, order_by=("-datetime_created", "-dataset", "-retention"))
			RequestConfig(request, paginate={'per_page': 25}).configure(table)
			context['table'] = table
		return render(request, self.template_name, context)


class TakeSnapshotView(LoginRequiredMixin, generic.View):
	template_name = 'ZFSAdmin/take_snapshot.html'

	def get(self, request, *args, **kwargs):
		#  note: options list corresponds to [value, label]
		choices = [(ds.dataset_name, ds.dataset_name) for ds in ZfsDatasets.objects.all()]
		form = DatasetSelection(choices=choices)
		return render(request, self.template_name, {'form': form})

	def post(self, request, *args, **kwargs):
		# create form instance and populate  with data from request:
		logger.error('TEST: {}'.format(request.POST.getlist('datasets')))

		choices = []
		for ds in request.POST.getlist('datasets'):
			choices.append((ds, ds))

		form = DatasetSelection(request.POST, choices=choices)
		# check valid:
		if form.is_valid():
			chosen_datasets = form.cleaned_data.get('datasets')
			# take the snapshots_demo.txt
			take_snapshot_task = async(engineering.take_snapshots,
			                           chosen_datasets, hook='ZFSAdmin.hooks.take_snapshots_callback')
			if take_snapshot_task:
				TaskManager.objects.update_or_create(task_id=take_snapshot_task,
				                                     process_id='snapshot_taker')
				return redirect('ZFSAdmin:index')
			else:
				message = 'An error occurred; snapshotting was not initialized!'
				return render(request, 'ZFSAdmin/take_snapshot.html', {'form': form,
				                                                       'message': message})
		else:
			message = 'There was a problem submitting the form; snapshots_demo.txt not taken. {}'
			return render(request, self.template_name, {'form': form,
			                                            'message': message})


@login_required
def update_snapshot_list(request):
	try:
		# if update task already running, just return the task id
		update_task = TaskManager.objects.get(process_id='snapshot_updater')
		return JsonResponse({'updating': 'true', 'task_id': update_task.task_id})
	except TaskManager.DoesNotExist:
		# if no task currently running, run the update task
		update_task = async(engineering.update_all_zfs_data, hook='ZFSAdmin.hooks.update_callback')
		TaskManager.objects.update_or_create(task_id=update_task, process_id='snapshot_updater')
		return JsonResponse({'updating': 'true', 'task_id': update_task})


@login_required
def delete_snapshots(request):
	if request.is_ajax():
		try:
			if request.method == 'POST':
				# convert the posted JSON into a list
				delete_list = []
				# decode binary request.body data to utf-8
				body_unicode = request.body.decode('utf-8')
				# load the decoded data into json format
				received_json = json.loads(body_unicode)
				for d in received_json["0"]["sendData"]:
					delete_list.append(d)
				update_task = async(engineering.delete_snapshots, delete_list, hook='ZFSAdmin.hooks.delete_callback')
				if update_task:
					TaskManager.objects.update_or_create(task_id=update_task, process_id='snapshot_deleter')
					return JsonResponse({'success': 'true'})
				else:
					return JsonResponse({'success': 'false', 'error': 'Update task initiation failed!'})
			else:
				return JsonResponse({'success': 'false', 'error': 'Request was not POST'})
		except (json.JSONDecodeError, AttributeError, TypeError, Exception) as e:
			return JsonResponse({'success': 'false', 'error': str(e)})
	else:
		return JsonResponse({'success': 'false', 'error': 'Request not Ajax'})


@login_required
def snapshot_task_manager(request):
	# this view is called exclusively from AJAX running on zfs_list_base.html
	page_load = request.GET.get('page_load')
	running_tasks = TaskManager.objects.all()
	snapshot_updater = running_tasks.filter(process_id='snapshot_updater')
	snapshot_deleter = running_tasks.filter(process_id='snapshot_deleter')
	snapshot_taker = running_tasks.filter(process_id='snapshot_taker')
	# if running task
	if snapshot_updater.filter(complete=False):  # if snapshot updater task running
		return JsonResponse({'updating': 'true', 'error': 'false', 'page_load': page_load})
	elif snapshot_deleter.filter(complete=False):
		return JsonResponse({'updating': 'true', 'error': 'false', 'page_load': page_load})
	elif snapshot_taker.filter(complete=False):
		return JsonResponse({'updating': 'true', 'error': 'false', 'page_load': page_load})
	# if running task now complete
	elif snapshot_updater.filter(complete=True):
		if snapshot_updater.filter(error_flag=True):
			error_detail = snapshot_updater.filter(error_flag=True).first().error_detail
			snapshot_updater.delete()  # delete the erroneous task from the TaskManager
			return JsonResponse({'updating': 'false', 'error': 'true', 'page_load': page_load,
			                     'error_detail': error_detail if error_detail else 'unspecified'})
		else:
			snapshot_updater.delete()
			return JsonResponse({'updating': 'false', 'error': 'false', 'page_load': page_load})
	elif snapshot_deleter.filter(complete=True):
		if snapshot_deleter.filter(error_flag=True):
			error_detail = snapshot_deleter.filter(error_flag=True).first().error_detail
			snapshot_deleter.delete()
			return JsonResponse({'updating': 'false', 'error': 'true', 'page_load': page_load,
			                     'error_detail': error_detail if error_detail else 'unspecified'})
		else:
			snapshot_deleter.delete()
			update_snapshot_list(request)  # initiate update to refresh the snapshot list
			return JsonResponse(
				{'updating': 'true', 'error': 'false', 'page_load': page_load})  # respond still updating
	elif snapshot_taker.filter(complete=True):
		if snapshot_taker.filter(error_flag=True):
			error_detail = snapshot_taker.filter(error_flag=True).first().error_detail
			snapshot_taker.delete()
			return JsonResponse({'updating': 'false', 'error': 'true', 'page_load': page_load,
			                     'error_detail': error_detail if error_detail else 'unspecified'})
		else:
			snapshot_taker.delete()
			update_snapshot_list(request)  # initiate update to refresh the snapshot list
			return JsonResponse(
				{'updating': 'true', 'error': 'false', 'page_load': page_load})  # respond still updating
	else:  # if no currently running tasks exist (and none have just been completed)
		return JsonResponse({'updating': 'false', 'error': 'false', 'page_load': page_load})
