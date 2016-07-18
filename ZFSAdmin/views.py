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
from .forms import *

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
logger = logging.getLogger(__name__)

NUMBER_OF_FORMS_IN_FORMSET = 5

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
                    # snapshot data
                    for ss in task_result[0]:
                        snapshot_datasets.append(ss.get('dataset'))
                        if request.GET.get('filter') and ss.get('dataset') == request.GET.get('filter'):
                            snapshots.append({'name': ss.get('name'),
                                              'retention': ss.get('retention'),
                                              'dataset': ss.get('dataset'),
                                              'datetime_created': ss.get('datetime_created')})
                        elif not request.GET.get('filter') or request.GET.get('filter') == 'all':
                            snapshots.append({'name': ss.get('name'),
                                              'retention': ss.get('retention'),
                                              'dataset': ss.get('dataset'),
                                              'datetime_created': ss.get('datetime_created')})
                    # file systems & snapshot data
                    for k, v in task_result[1].items():
                        filesystems.append(k)
                    table = SnapshotTable(snapshots, order_by=("-datetime_created", "-dataset", "-retention"))
                    RequestConfig(request, paginate={'per_page': 25}).configure(table)
                    context['table'] = table
                    # shared panes data
                    context['formset_forms'] = NUMBER_OF_FORMS_IN_FORMSET
                    context['datasets'] = sorted(set(filesystems))
                    dataset_choices = [(fs, fs) for fs in sorted(set(filesystems))]
                    context['dataset_form'] = DatasetForm(choices=dataset_choices,
                                                          initial=dataset_choices[0][1])
                    compression = sorted([('on', 'On (default type)'), ('off', 'Off'), ('lzjb', 'lzjb'),
                                          ('gzip', 'gzip'), ('zle', 'zle'), ('lz4', 'lz4')])
                    # file system properties pane
                    context['properties'] = task_result[1]
                    # dataset creation pane
                    new_filesystem_formset = formset_factory(ManageFileSystems, extra=context.get('formset_forms'))
                    context['formset'] = new_filesystem_formset(
                        form_kwargs={'dataset_choices': dataset_choices,
                                     'compression_choice': compression,
                                     'initial_compression': 'on',
                                     'initial_dataset': dataset_choices[0][1]})
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
    logger.error(request.GET.get('task_id'))
    task_result = q_result(request.GET.get('task_id'))
    logger.error(str(task_result))
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
            form = DatasetForm(request.POST, choices=[(request.POST.get('datasets'), request.POST.get('datasets'))])
            if form.is_valid():
                delete_task = async(engineering.delete_filesystem, [form.cleaned_data['datasets']])
                if delete_task:
                    return HttpResponse(str(delete_task))
            else:
                return HttpResponseServerError
    return HttpResponseServerError


@user_passes_test(lambda u: u.is_superuser)
def manage_filesystem(request):
    user = request.user  # necessary for the @user_passes_test decorator
    if request.is_ajax():
        if request.method == 'POST':
            datasets_chosen = []
            compression_chosen = []
            new_filesystem_formset = formset_factory(ManageFileSystems, extra=NUMBER_OF_FORMS_IN_FORMSET)
            for form_num in range(NUMBER_OF_FORMS_IN_FORMSET):
                datasets_chosen.append([request.POST.get('form-{}-datasets'.format(form_num)),
                                        request.POST.get('form-{}-datasets'.format(form_num))])
                compression_chosen.append([request.POST.get('form-{}-compression'.format(form_num)),
                                           ('form-{}-compression'.format(form_num))])
            formset = new_filesystem_formset(request.POST, form_kwargs={'dataset_choices': datasets_chosen,
                                                                        'compression_choice': compression_chosen})
            if formset.is_valid():
                if not formset.cleaned_data[0]['edit_mode']:
                    # only send 1st form - edit mode only uses 1 instance of formset, rest are obsolete
                    create_task = async(engineering.create_filesystems, data=formset.cleaned_data)
                else:
                    create_task = async(engineering.edit_filesystems, data=formset.cleaned_data[0])
                if create_task:
                    return HttpResponse(str(create_task))
                else:
                    return HttpResponseServerError
            else:
                error_str = ''
                for e in formset.errors:
                    for k, v in e.items():
                        logger.error(k + '>>>' + v)
                        er_str = ''
                        for er in v:
                            er_str += '{}, '.format(er)
                        error_str += '{}, '.format(er_str.strip(', '))
                return HttpResponse('ERROR: ' + error_str.strip(', '))
    return HttpResponseServerError
