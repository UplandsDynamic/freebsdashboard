#!/usr/bin/env python3
import os
import sys
import logging
from django.views import generic
from django.shortcuts import render
from django_tables2 import RequestConfig
from django_q.tasks import async, result as q_result
from django.http import JsonResponse, HttpResponse, HttpResponseServerError
from .tables import SnapshotTable
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import ZFSAdmin.engineering as engineering
import json
from django.contrib.auth.decorators import user_passes_test
from django.forms import formset_factory
from .forms import ManageFileSystems, DatasetDeletion

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
logger = logging.getLogger(__name__)

'''SNAPSHOT DISPLAY VIEW'''


class IndexView(LoginRequiredMixin, generic.View):
    TEMPLATE_NAME = 'ZFSAdmin/snapshot_table.html'
    SNAPSHOT_DELETE_PROCESS = 'snapshot_delete'
    SNAPSHOT_UPDATE_PROCESS = 'snapshot_update'
    SNAPSHOT_CLONE_PROCESS = 'snapshot_clone'
    SNAPSHOT_TAKE_PROCESS = 'snapshot_take'
    FILESYSTEM_MANAGEMENT_PROCESS = 'filesystem_management'

    def get(self, request):
        # set timezone to UTC if not already set to something else
        if 'django_timezone' not in request.session:
            request.session['django_timezone'] = 'UTC'
        context = {}
        snapshots = []
        filesystems = []
        snapshot_datasets = []
        if request.GET.get('task_id'):
            process = request.GET.get('process')
            context['task_id'] = request.GET.get('task_id')
            context['stop_updating'] = 'true'
            task_result = q_result(request.GET.get('task_id'))
            if process == self.SNAPSHOT_UPDATE_PROCESS:
                # build the snapshot table ...
                if task_result:
                    for result in task_result:
                        if 'process_result_snapshots' in result:
                            pr = result.get('process_result_snapshots')
                            snapshot_datasets.append(pr.get('dataset'))
                            if request.GET.get('filter') and pr.get('dataset') == request.GET.get('filter'):
                                snapshots.append({'name': pr.get('name'),
                                                  'retention': pr.get('retention'),
                                                  'dataset': pr.get('dataset'),
                                                  'datetime_created': pr.get('datetime_created')})
                            elif not request.GET.get('filter') or request.GET.get('filter') == 'all':
                                snapshots.append({'name': pr.get('name'),
                                                  'retention': pr.get('retention'),
                                                  'dataset': pr.get('dataset'),
                                                  'datetime_created': pr.get('datetime_created')})
                        if 'process_result_filesystems' in result:
                            filesystems.append(result.get('process_result_filesystems').get('filesystem_name'))
                    table = SnapshotTable(snapshots, order_by=("-datetime_created", "-dataset", "-retention"))
                    RequestConfig(request, paginate={'per_page': 25}).configure(table)
                    context['table'] = table
                    context['datasets'] = sorted(set(filesystems))
                    # dataset management pane
                    context['formset_forms'] = 5
                    choices = [(fs, fs) for fs in sorted(set(filesystems))]
                    new_filesystem_formset = formset_factory(ManageFileSystems, extra=context.get('formset_forms'))
                    context['formset'] = new_filesystem_formset(
                        form_kwargs={'choices': choices, 'initial': choices[0][1]})
                    context['dataset_deletion_form'] = DatasetDeletion(choices=choices, initial=choices[0][1])
                    # render the template
                    return render(request, self.TEMPLATE_NAME, context)
                else:
                    context['message'] = 'There appears to have been an issue updating the snapshot list!'
                    return render(request, self.TEMPLATE_NAME, context)
        # if returning results from completed update process, start an update (and render template)
        return self.update(request)

    def update(self, request):
        # start task to grab snapshots and datasets & send task_ids to AJAX in template via context
        context = {'task_id': async(engineering.update_zfs_data), 'updating': 'true', 'stop_updating': 'false'}
        return render(request, self.TEMPLATE_NAME, context)


@login_required
def task_checker(request):
    task_result = q_result(request.GET.get('task_id'))
    error = 'false'
    error_blurb = ''
    if task_result:
        updating = 'false'
        if isinstance(task_result, list):
            for r in task_result:
                if 'error' in r and r.get('error') != 'Password:':
                    error = 'true'
                    error_blurb += '{}..., '.format(r.get('error')[0:101].replace('Password:', ''))
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
                delete_task = async(engineering.delete_snapshots, delete_list)
                if delete_task:
                    return JsonResponse({'success': 'true', 'task_id': delete_task})
                else:
                    return JsonResponse({'success': 'false', 'error': 'Delete snapshot(s) initiation failed!'})
        except (json.JSONDecodeError, AttributeError, TypeError, Exception) as e:
            return JsonResponse({'success': 'false', 'error': str(e)})
    return JsonResponse({'success': 'false', 'error': 'Inappropriate request (not Ajax or POST)'})


@user_passes_test(lambda u: u.is_superuser)
def clone_snapshots(request):
    user = request.user  # necessary for the @user_passes_test decorator
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
                clone_task = async(engineering.clone_snapshots, clone_list)
                if clone_task:
                    return JsonResponse({'success': 'true', 'task_id': clone_task})
                else:
                    return JsonResponse({'success': 'false', 'error': 'Clone initiation failed!'})
        except (json.JSONDecodeError, AttributeError, TypeError, Exception) as e:
            return JsonResponse({'success': 'false', 'error': str(e)})
    return JsonResponse({'success': 'false', 'error': 'Inappropriate request (not Ajax or POST)'})


@user_passes_test(lambda u: u.is_superuser)
def take_snapshots(request):
    user = request.user  # necessary for the @user_passes_test decorator
    if request.is_ajax():
        try:
            if request.method == 'POST':
                # convert the posted JSON into a list
                dataset_list = []
                # decode binary request.body data to utf-8
                body_unicode = request.body.decode('utf-8')
                # load the decoded data into json format
                received_json = json.loads(body_unicode)
                for d in received_json["0"]["sendData"]:
                    dataset_list.append(d)
                take_snapshots_tast = async(engineering.take_snapshots, dataset_list)
                if take_snapshots_tast:
                    return JsonResponse({'success': 'true', 'task_id': take_snapshots_tast})
                else:
                    return JsonResponse({'success': 'false', 'error': 'Take snaphot task failed!'})
        except (json.JSONDecodeError, AttributeError, TypeError, Exception) as e:
            return JsonResponse({'success': 'false', 'error': str(e)})
    return JsonResponse({'success': 'false', 'error': 'Inappropriate request (not Ajax or POST)'})


@user_passes_test(lambda u: u.is_superuser)
def delete_filesystem(request):
    user = request.user  # necessary for the @user_passes_test decorator
    if request.is_ajax():
        if request.method == 'POST':
            logger.error(request.POST.get('datasets'))
            form = DatasetDeletion(request.POST, choices=[(request.POST.get('datasets'), request.POST.get('datasets'))])
            if form.is_valid():
                delete_task = async(engineering.delete_filesystem, [form.cleaned_data['datasets']])
                if delete_task:
                    return HttpResponse(str(delete_task))
            else:
                logger.error('here')
                return HttpResponseServerError
    return HttpResponseServerError


@user_passes_test(lambda u: u.is_superuser)
def create_filesystem(request):
    user = request.user  # necessary for the @user_passes_test decorator
    if request.is_ajax():
        if request.method == 'POST':
            chosen = []
            logger.error(str(request.POST))
            new_filesystem_formset = formset_factory(ManageFileSystems, extra=5)
            for form_num, data in enumerate(request.POST):
                chosen.append([request.POST.get('form-{}-datasets'.format(form_num)),
                               request.POST.get('form-{}-datasets'.format(form_num))])
            formset = new_filesystem_formset(request.POST, form_kwargs={'choices': chosen})
            if formset.is_valid():
                create_task = async(engineering.create_filesystems, data=formset.cleaned_data)
                if create_task:
                    return HttpResponse(str(create_task))
                else:
                    return HttpResponseServerError
    return HttpResponseServerError

