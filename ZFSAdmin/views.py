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
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import ZFSAdmin.engineering as engineering
from .forms import FileSystemSelection, NewFileSystem
import json
from django.contrib.auth.decorators import user_passes_test
from django.forms import formset_factory

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
logger = logging.getLogger(__name__)


class IndexView(LoginRequiredMixin, generic.View):
    TEMPLATE_NAME = 'ZFSAdmin/snapshot_table.html'

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
        return render(request, self.TEMPLATE_NAME, context)


class TakeSnapshotView(UserPassesTestMixin, generic.View):
    TEMPLATE_NAME = 'ZFSAdmin/take_snapshot.html'
    PENDING_TASK = 'PENDING_SNAPSHOT_TAKER'
    PROCESS_ID = 'snapshot_taker'

    def test_func(self):
        # checks user is superuser; if not redirects to login
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        #  note: options list corresponds to [value, label]
        choices = [(fs.filesystem_name, fs.filesystem_name) for fs in ZfsFileSystems.objects.all()]
        form = FileSystemSelection(choices=choices)
        return render(request, self.TEMPLATE_NAME, {'form': form})

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
            TaskManager.objects.create(task_id=self.PENDING_TASK, process_id=self.PROCESS_ID, complete=False)
            take_snapshot_task = async(engineering.take_snapshots,
                                       chosen_filesystems, hook='ZFSAdmin.hooks.take_snapshots_callback')
            if take_snapshot_task:
                # update the task with the task_id
                TaskManager.objects.filter(task_id=self.PENDING_TASK).update(
                    task_id=take_snapshot_task, process_id=self.PROCESS_ID)
                # return to index
                return redirect('ZFSAdmin:index')
            else:
                message = 'An error occurred; snapshotting was not initialized!'
                TaskManager.objects.filter(task_id=self.PENDING_TASK).delete()
                return render(request, self.TEMPLATE_NAME, {'form': form,
                                                            'message': message})
        else:
            message = 'There was a problem submitting the form; snapshots not taken. {}'
            return render(request, self.TEMPLATE_NAME, {'form': form,
                                                        'message': message})


class ChangeFileSystems(UserPassesTestMixin, generic.View):
    TEMPLATE_NAME = 'ZFSAdmin/change_filesystems.html'
    PENDING_TASK = 'PENDING_FILESYSTEM_CREATOR'
    PROCESS_ID = 'filesystem_creator'

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        existing_filesystems = ZfsFileSystems.objects.all()
        datasets = existing_filesystems.values_list('filesystem_name', flat=True).order_by('filesystem_name')
        choices = [(ds, ds) for ds in datasets]
        new_filesystem_formset = formset_factory(NewFileSystem, extra=5)
        formset = new_filesystem_formset(
            form_kwargs={'choices': choices, 'initial': choices[0][1]})  # n.b. in this case [0] & [1] are same anyway
        dataset_deletion_form = NewFileSystem(choices=choices, initial=choices[0][1])
        return render(request, self.TEMPLATE_NAME,
                      {'formset': formset, 'dataset_deletion_form': dataset_deletion_form, 'datasets': datasets})

    def post(self, request, *args, **kwargs):
        existing_filesystems = ZfsFileSystems.objects.all()
        new_filesystem_formset = formset_factory(NewFileSystem, extra=5)
        chosen = []
        for form_num, data in enumerate(request.POST):
            chosen.append([request.POST.get('form-{}-datasets'.format(form_num)),
                           request.POST.get('form-{}-datasets'.format(form_num))])
        formset = new_filesystem_formset(request.POST, form_kwargs={'choices': chosen})
        # check valid:
        if formset.is_valid():
            # place task in the manager early to avoid race conditions
            TaskManager.objects.create(task_id=self.PENDING_TASK, process_id=self.PROCESS_ID, complete=False)
            create_filesystems_task = async(engineering.create_filesystems,
                                            data=formset.cleaned_data,
                                            hook='ZFSAdmin.hooks.create_filesystems_callback')
            if create_filesystems_task:
                # update the taskmanager with the task id
                TaskManager.objects.filter(task_id=self.PENDING_TASK).update(
                    task_id=create_filesystems_task, process_id=self.PROCESS_ID)
                return redirect('ZFSAdmin:index')
            else:
                message = 'An error occurred; file systems were not created!'
                TaskManager.objects.filter(task_id=self.PENDING_TASK).delete()
                return render(request, self.TEMPLATE_NAME, {'formset': formset, 'message': message})
        else:
            message = 'There was a problem submitting the form; filesystems not created!'
            datasets = existing_filesystems.values_list('filesystem_name', flat=True).order_by('filesystem_name')
            choices = [(ds, ds) for ds in datasets]
            # note, dataset deletion form NOT submitted via POST - handled by AJAX, so return new form (no existing value returned)
            dataset_deletion_form = NewFileSystem(choices=choices, initial=choices[0][1])
            formset = new_filesystem_formset(request.POST,
                                             form_kwargs={'choices': choices, 'initial': choices[0][1]})
            return render(request, self.TEMPLATE_NAME, {'formset': formset,
                                                        'dataset_deletion_form': dataset_deletion_form,
                                                        'message': message})


@login_required
def update_snapshot_list(request):
    pending_task = 'PENDING_SNAPSHOT_UPDATE'
    process_id = 'snapshot_updater'
    try:
        # if update task already running, just return the task id
        update_task = TaskManager.objects.get(process_id=process_id)
        return JsonResponse({'updating': 'true', 'task_id': update_task.task_id})
    except TaskManager.DoesNotExist:
        # if no task currently running, run the update task
        TaskManager.objects.update_or_create(task_id=pending_task, process_id=process_id)
        update_task = async(engineering.update_all_zfs_data, hook='ZFSAdmin.hooks.update_callback')
        TaskManager.objects.filter(task_id=pending_task).update(task_id=update_task, process_id=process_id)
        return JsonResponse({'updating': 'true', 'task_id': update_task})


@user_passes_test(lambda u: u.is_superuser)
def delete_snapshots(request):
    user = request.user  # necessary for the @user_passes_test decorator
    pending_task = 'PENDING_SNAPSHOT_DELETE'
    process_id = 'snapshot_deleter'
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
                # place task in the manager early to avoid race conditions
                TaskManager.objects.update_or_create(task_id=pending_task, process_id=process_id)
                delete_task = async(engineering.delete_snapshots, delete_list,
                                    hook='ZFSAdmin.hooks.delete_callback')
                if delete_task:
                    # update the taskmanager with the task id
                    TaskManager.objects.filter(task_id=pending_task).update(task_id=delete_task,
                                                                            process_id=process_id)
                    return JsonResponse({'success': 'true'})
                else:
                    TaskManager.objects.filter(task_id=pending_task).delete()
                    return JsonResponse({'success': 'false', 'error': 'Update task initiation failed!'})
            else:
                return JsonResponse({'success': 'false', 'error': 'Request was not POST'})
        except (json.JSONDecodeError, AttributeError, TypeError, Exception) as e:
            return JsonResponse({'success': 'false', 'error': str(e)})
    else:
        return JsonResponse({'success': 'false', 'error': 'Request not Ajax'})


@user_passes_test(lambda u: u.is_superuser)
def clone_snapshots(request):
    user = request.user  # necessary for the @user_passes_test decorator
    pending_task = 'PENDING_SNAPSHOT_CLONE'
    process_id = 'snapshot_cloner'
    if request.is_ajax():
        try:
            if request.method == 'POST':
                # convert the posted JSON into a list
                clone_list = []
                # decode binary request.body data to utf-8
                body_unicode = request.body.decode('utf-8')
                # load the decoded data into json format
                received_json = json.loads(body_unicode)
                for d in received_json["0"]["sendData"]:
                    clone_list.append(d)
                # place task in the manager early to avoid race conditions
                TaskManager.objects.update_or_create(task_id=pending_task, process_id=process_id)
                clone_task = async(engineering.clone_snapshots, clone_list,
                                   hook='ZFSAdmin.hooks.clone_callback')
                if clone_task:
                    # update the taskmanager with the task id
                    TaskManager.objects.filter(task_id=pending_task).update(task_id=clone_task,
                                                                            process_id=process_id)
                    return JsonResponse({'success': 'true'})
                else:
                    TaskManager.objects.filter(task_id=pending_task).delete()
                    return JsonResponse({'success': 'false', 'error': 'Update task initiation failed!'})
            else:
                return JsonResponse({'success': 'false', 'error': 'Request was not POST'})
        except (json.JSONDecodeError, AttributeError, TypeError, Exception) as e:
            return JsonResponse({'success': 'false', 'error': str(e)})
    else:
        return JsonResponse({'success': 'false', 'error': 'Request not Ajax'})


@user_passes_test(lambda u: u.is_superuser)
def delete_filesystem(request):
    user = request.user  # necessary for the @user_passes_test decorator
    pending_task = 'PENDING_FILESYSTEM_DELETE'
    process_id = 'filesystem_deleter'
    if request.is_ajax():
        try:
            if request.method == 'POST':
                # decode binary request.body data to utf-8
                body_unicode = request.body.decode('utf-8')
                # load the decoded data into json format
                received_json = json.loads(body_unicode)["0"]["sendData"]
                TaskManager.objects.update_or_create(task_id=pending_task, process_id=process_id)
                delete_task = async(engineering.delete_filesystem, received_json,
                                    hook='ZFSAdmin.hooks.fs_delete_callback')
                if delete_task:
                    TaskManager.objects.filter(task_id=pending_task).update(task_id=delete_task,
                                                                            process_id=process_id)
                    return JsonResponse({'success': 'true'})
                else:
                    TaskManager.objects.filter(task_id=pending_task).delete()
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
    snapshot_cloner = running_tasks.filter(process_id='snapshot_cloner')
    snapshot_taker = running_tasks.filter(process_id='snapshot_taker')
    filesystem_creator = running_tasks.filter(process_id='filesystem_creator')
    filesystem_deleter = running_tasks.filter(process_id='filesystem_deleter')
    # if running task
    if snapshot_updater.filter(complete=False) or \
            snapshot_deleter.filter(complete=False) or \
            snapshot_cloner.filter(complete=False) or \
            snapshot_taker.filter(complete=False) or \
            filesystem_creator.filter(complete=False) or \
            filesystem_deleter.filter(complete=False):
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
        if snapshot_cloner.filter(error_flag=True):
            error_detail = snapshot_cloner.filter(error_flag=True).first().error_detail
            snapshot_cloner.delete()
        if filesystem_creator.filter(error_flag=True):
            error_detail = filesystem_creator.filter(error_flag=True).first().error_detail
            filesystem_creator.delete()
            update_snapshot_list(request)  # initiate update to refresh the snapshot list
            updating = 'true'
        if filesystem_deleter.filter(error_flag=True):
            filesystem_deleter.delete()
        return JsonResponse({'updating': updating, 'error': 'true', 'page_load': page_load,
                             'error_detail': error_detail if error_detail else 'unspecified'})
    # if running tasks now complete and no errors
    if snapshot_updater.filter(error_flag=False):
        snapshot_updater.delete()
    if snapshot_deleter.filter(error_flag=False):
        update_snapshot_list(request)  # initiate update to refresh the snapshot list
        updating = 'true'
    if snapshot_cloner.filter(error_flag=False):
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
    if filesystem_deleter.filter(error_flag=False):
        filesystem_deleter.delete()
        update_snapshot_list(request)
        updating = 'true'
    return JsonResponse(
        {'updating': updating, 'error': 'false', 'page_load': page_load})  # respond still updating
