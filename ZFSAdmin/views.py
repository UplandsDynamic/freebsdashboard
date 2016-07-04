#!/usr/bin/env python3
import os
import sys
import logging
from django.conf import settings
from django.views import generic
from django.shortcuts import render
from django_tables2 import RequestConfig
from django_q.tasks import async, result as q_result
from django.http import JsonResponse
from django.shortcuts import redirect
from .models import TaskManager, ZfsFileSystems
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

'''SNAPSHOT DISPLAY VIEW'''


class IndexView(LoginRequiredMixin, generic.View):
    TEMPLATE_NAME = 'ZFSAdmin/snapshot_table.html'

    def get(self, request):
        context = {}
        if request.GET.get('task_id'):
            # once ajax call to snapshot_update() returns data from async task...
            context['updating'] = 'false'
            task_result = q_result(request.GET.get('task_id'))
            snapshots = []
            if task_result:
                for result in task_result:
                    if 'process_result' in result:
                        pr = result.get('process_result')
                        snapshots.append({'name': pr.get('name'),
                                          'retention': pr.get('retention'),
                                          'dataset': pr.get('dataset'),
                                          'datetime_created': pr.get('datetime_created')})
                    # # return only a subset of filtered results if necessary
                    # if request.GET.get('filter'):
                    #     snapshots =  TODO...
                table = SnapshotTable(snapshots, order_by=("-datetime_created", "-dataset", "-retention"))
                RequestConfig(request, paginate={'per_page': 25}).configure(table)
                context['table'] = table
                return render(request, self.TEMPLATE_NAME, context)
            else:
                context['message'] = 'There appears to have been an issue updating the snapshot list!'
                return render(request, self.TEMPLATE_NAME, context)
        else:
            # set timezone to UTC if not already set to something else
            if 'django_timezone' not in request.session:
                request.session['django_timezone'] = 'UTC'
            # start task to grab snapshots and datasets & send task_ids to AJAX in template via context
            context['snapshot_task'] = async(engineering.update_zfs_data, 'LIST_SNAPSHOTS')
            # context['datasets_task'] = async(engineering.update_zfs_data, 'FILE_SYSTEMS')  # TODO...
            context['updating'] = 'true'
            return render(request, self.TEMPLATE_NAME, context)


@login_required
def snapshot_update(request):
    task_result = q_result(request.GET.get('task_id'))
    logger.error('TASK ID: {} | TASK RESULT: {}'.format(request.GET.get('task_id'), str(task_result)))
    error = 'false'
    error_blurb = ''
    if task_result:
        updating = 'false'
        if isinstance(task_result, list):
            for r in task_result:
                if 'error' in r:
                    error = 'true'
                    error_blurb += '{}, '.format(r.get('error'))
        else:
            error = 'true'
            error_blurb = task_result
    else:
        updating = 'true'
    return JsonResponse({'updating': updating, 'error': error,
                         'error_detail': error_blurb.rstrip(', ') if error_blurb else 'unspecified'})


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


'''TAKE SNAPSHOT VIEW'''


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


'''CHANGE FILESYSTEM VIEW'''


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
