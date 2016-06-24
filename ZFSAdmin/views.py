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
from .models import TaskManager, ZfsSnapshot, ZfsFileSystems
from .tables import SnapshotTable
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import ZFSAdmin.engineering as engineering
from .forms import FileSystemSelection, NewFileSystem
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
		choices = [(fs.filesystem_name, fs.filesystem_name) for fs in ZfsFileSystems.objects.all()]
		form = FileSystemSelection(choices=choices)
		return render(request, self.template_name, {'form': form})

	def post(self, request, *args, **kwargs):
		# create form instance and populate  with data from request:

		choices = []
		for fs in request.POST.getlist('filesystems'):
			choices.append((fs, fs))

		form = FileSystemSelection(request.POST, choices=choices)
		# check valid:
		if form.is_valid():
			chosen_filesystems = form.cleaned_data.get('filesystems')
			# place task in the manager early to avoid race conditions
			TaskManager.objects.create(task_id="PENDING_SNAPSHOT_TAKER",
			                           process_id='snapshot_taker', complete=False)
			take_snapshot_task = async(engineering.take_snapshots,
			                           chosen_filesystems, hook='ZFSAdmin.hooks.take_snapshots_callback')
			if take_snapshot_task:
				# update the task with the task_id
				TaskManager.objects.filter(task_id='PENDING_SNAPSHOT_TAKER').update(
					task_id=take_snapshot_task, process_id='snapshot_taker')
				# return to index
				return redirect('ZFSAdmin:index')
			else:
				message = 'An error occurred; snapshotting was not initialized!'
				TaskManager.objects.filter(task_id='PENDING_SNAPSHOT_TAKER').delete()
				return render(request, self.template_name, {'form': form,
				                                            'message': message})
		else:
			message = 'There was a problem submitting the form; snapshots not taken. {}'
			return render(request, self.template_name, {'form': form,
			                                            'message': message})


class CreateFileSystems(LoginRequiredMixin, generic.View):
	template_name = 'ZFSAdmin/create_filesystem.html'

	def get(self, request, *args, **kwargs):
		existing_filesystems = ZfsFileSystems.objects.all()
		filesystem_names = existing_filesystems.values_list('filesystem_name', flat=True).order_by('filesystem_name')
		zpools = set(existing_filesystems.values_list('zpool', flat=True).reverse())
		choices = [(zp, zp) for zp in zpools]
		form = NewFileSystem(choices=choices, initial=choices[0][1])  # n.b. in this case [0] & [1] are same anyway.
		return render(request, self.template_name, {'form': form, 'filesystems': filesystem_names,
		                                            'zpools': zpools})

	def post(self, request, *args, **kwargs):
		existing_filesystems = ZfsFileSystems.objects.all()
		filesystem_names = existing_filesystems.values_list('filesystem_name', flat=True).order_by('filesystem_name')
		chosen = [(request.POST.get('zpools'), request.POST.get('zpools'))]
		existing_filesystems = ZfsFileSystems.objects.all()
		form = NewFileSystem(request.POST, choices=chosen)
		# check valid:
		if form.is_valid():
			# place task in the manager early to avoid race conditions
			TaskManager.objects.create(task_id="PENDING_FILESYSTEM_CREATOR",
			                           process_id='filesystem_creator', complete=False)
			create_filesystems_task = async(engineering.create_filesystems,
			                                names=form.cleaned_data.get('filesystems'),
			                                zpool=form.cleaned_data.get('zpools'),
			                                hook='ZFSAdmin.hooks.create_filesystems_callback')
			if create_filesystems_task:
				# update the taskmanager with the task id
				TaskManager.objects.filter(task_id='PENDING_FILESYSTEM_CREATOR').update(
					task_id=create_filesystems_task, process_id='filesystem_creator')
				return redirect('ZFSAdmin:index')
			else:
				message = 'An error occurred; file systems were not created!'
				TaskManager.objects.filter(task_id='PENDING_FILESYSTEM_CREATOR').delete()
				return render(request, self.template_name, {'form': form,
				                                            'message': message,
				                                            'existing': existing_filesystems})
		else:
			message = 'There was a problem submitting the form; filesystems not created.'
			zpools = set(existing_filesystems.values_list('zpool', flat=True).order_by('zpool'))
			choices = [(zp, zp) for zp in zpools]
			form = NewFileSystem(request.POST, choices=choices, initial=chosen)
			return render(request, self.template_name, {'form': form,
			                                            'message': message,
			                                            'filesystems': filesystem_names,
			                                            'zpools': zpools})


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
	updating = 'false'
	# this view is called exclusively from AJAX running on zfs_list_base.html
	page_load = request.GET.get('page_load')
	running_tasks = TaskManager.objects.all()
	snapshot_updater = running_tasks.filter(process_id='snapshot_updater')
	snapshot_deleter = running_tasks.filter(process_id='snapshot_deleter')
	snapshot_taker = running_tasks.filter(process_id='snapshot_taker')
	filesystem_creator = running_tasks.filter(process_id='filesystem_creator')
	# if running task
	if snapshot_updater.filter(complete=False) or \
			snapshot_deleter.filter(complete=False) or \
			snapshot_taker.filter(complete=False) or \
			filesystem_creator.filter(complete=False):
		return JsonResponse({'updating': 'true', 'error': 'false', 'page_load': page_load})
	# if running tasks now complete but errors:
	error_detail = ''
	if running_tasks.filter(error_flag=True).exists():
		if snapshot_updater.filter(error_flag=True):
			error_detail = snapshot_updater.filter(error_flag=True).first().error_detail
			snapshot_updater.delete()  # delete the erroneous task from the TaskManager
		if snapshot_taker.filter(error_flag=True):
			error_detail = snapshot_taker.filter(error_flag=True).first().error_detail
			snapshot_taker.delete()
		if snapshot_deleter.filter(error_flag=True):
			error_detail = snapshot_deleter.filter(error_flag=True).first().error_detail
			snapshot_deleter.delete()
		if filesystem_creator.filter(error_flag=True):
			error_detail = filesystem_creator.filter(error_flag=True).first().error_detail
			filesystem_creator.delete()
			update_snapshot_list(request)  # initiate update to refresh the snapshot list
			updating = 'true'
		return JsonResponse({'updating': updating, 'error': 'true', 'page_load': page_load,
		                     'error_detail': error_detail if error_detail else 'unspecified'})
	# if running tasks now complete and no errors
	if snapshot_updater.filter(error_flag=False):
		snapshot_updater.delete()
	if snapshot_deleter.filter(error_flag=False):
		update_snapshot_list(request)  # initiate update to refresh the snapshot list
		updating = 'true'
	if snapshot_taker.filter(error_flag=False):
		snapshot_taker.delete()
		update_snapshot_list(request)  # initiate update to refresh the snapshot list
		updating = 'true'
	if filesystem_creator.filter(error_flag=False):
		filesystem_creator.delete()
		update_snapshot_list(request)  # initiate update to refresh the snapshot list
		updating = 'true'
	return JsonResponse(
		{'updating': updating, 'error': 'false', 'page_load': page_load})  # respond still updating
