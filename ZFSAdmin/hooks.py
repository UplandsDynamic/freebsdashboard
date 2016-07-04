# hooks.py
from .models import TaskManager
import logging

logger = logging.getLogger(__name__)


def update_callback(task):
    process_id = 'snapshot_updater'
    error_blurb = 'Unable to display snapshots - do any exist?'
    # delete the task id from the task manager if no error, else add error flag
    if task.result is True:
        TaskManager.objects.update(task_id=task.id,
                                   process_id=process_id,
                                   error_flag=False,
                                   complete=True,
                                   error_detail=None,
                                   snapshots=task.result.get('snapshots'))
    else:
        TaskManager.objects.update(task_id=task.id,
                                   process_id=process_id,
                                   error_flag=True,
                                   complete=True,
                                   error_detail=error_blurb)


def delete_callback(task):
    process_id = 'snapshot_deleter'
    error = ''
    error_blurb = 'There was an error initiating the task; snapshots were not deleted!'
    if task.success:
        if task.result:
            for result in task.result:
                # Disregard "Password:" as an error - it's simply  passed to stderr during sudo -S process.
                if 'error' in result and result.get('error') != 'Password:':
                    error += '{}, '.format(result.get('error'))
        else:
            error = 'There was a problem running the operation - no result was received.'
        if error:
            TaskManager.objects.update(task_id=task.id,
                                       process_id=process_id,
                                       error_flag=True,
                                       error_detail=error.rstrip(', '),
                                       complete=True)
        else:
            TaskManager.objects.update(task_id=task.id,
                                       process_id=process_id,
                                       error_flag=False,
                                       error_detail=None,
                                       complete=True)
    else:
        TaskManager.objects.update(task_id=task.id,
                                   process_id=process_id,
                                   error_flag=True,
                                   error_detail=error_blurb,
                                   complete=True)


def clone_callback(task):
    process_id = 'snapshot_cloner'
    error = ''
    error_blurb = 'There was an error initiating the task; snapshots were not cloned!'
    if task.success:
        if task.result:
            for result in task.result:
                # Disregard "Password:" as an error - it's simply  passed to stderr during sudo -S process.
                if 'error' in result and result.get('error') != 'Password:':
                    error += '{}, '.format(result.get('error'))
        else:
            error = 'There was a problem running the operation - no result was received.'
        if error:
            TaskManager.objects.update(task_id=task.id,
                                       process_id=process_id,
                                       error_flag=True,
                                       error_detail=error.rstrip(', '),
                                       complete=True)
        else:
            TaskManager.objects.update(task_id=task.id,
                                       process_id=process_id,
                                       error_flag=False,
                                       error_detail=None,
                                       complete=True)
    else:
        TaskManager.objects.update(task_id=task.id,
                                   process_id=process_id,
                                   error_flag=True,
                                   error_detail=error_blurb,
                                   complete=True)


def fs_delete_callback(task):
    error = ''
    process_id = 'filesystem_deleter'
    error_blurb = 'There was an error initiating the task; filesystem was not deleted!'
    if task.success:
        if task.result:
            for result in task.result:
                # Disregard "Password:" as an error - it's simply  passed to stderr during sudo -S process.
                if 'error' in result and result.get('error') != 'Password:':
                    error += '{}, '.format(result.get('error'))
        else:
            error = 'There was a problem running the operation - no result was received.'
        if error:
            TaskManager.objects.update(task_id=task.id,
                                       process_id=process_id,
                                       error_flag=True,
                                       error_detail=error.rstrip(', '),
                                       complete=True)
        else:
            TaskManager.objects.update(task_id=task.id,
                                       process_id=process_id,
                                       error_flag=False,
                                       error_detail=None,
                                       complete=True)
    else:
        TaskManager.objects.update(task_id=task.id,
                                   process_id=process_id,
                                   error_flag=True,
                                   error_detail=error_blurb,
                                   complete=True)


def take_snapshots_callback(task):
    error = ''
    process_id = 'snapshot_taker'
    error_blurb = 'There was an error initiating the task; snapshots were not created!'
    if task.success:
        if task.result:
            for result in task.result:
                # Disregard "Password:" as an error - it's simply  passed to stderr during sudo -S process.
                if 'error' in result and result.get('error') != 'Password:':
                    error += '{}, '.format(result.get('error'))
        else:
            error = 'There was a problem running the operation - no result was received.'
        if error:
            TaskManager.objects.update(task_id=task.id,
                                       process_id=process_id,
                                       error_flag=True,
                                       error_detail=error.rstrip(', '),
                                       complete=True)
        else:
            TaskManager.objects.update(task_id=task.id,
                                       process_id=process_id,
                                       error_flag=False,
                                       error_detail=None,
                                       complete=True)
    else:
        TaskManager.objects.update(task_id=task.id,
                                   process_id=process_id,
                                   error_flag=True,
                                   error_detail=error_blurb,
                                   complete=True)


def create_filesystems_callback(task):
    error = ''
    error_blurb = 'There was an error initiating the task; file system was not created!'
    process_id = 'filesystem_creator'
    if task.success:
        if task.result:
            for result in task.result:
                # Disregard "Password:" as an error - it's simply  passed to stderr during sudo -S process.
                if 'error' in result and result.get('error') != 'Password:':
                    error += '{}, '.format(result.get('error'))
        else:
            error = 'There was a problem running the operation - no result was received.'
        if error:
            TaskManager.objects.update(task_id=task.id,
                                       process_id=process_id,
                                       error_flag=True,
                                       error_detail=error.rstrip(', '),
                                       complete=True)
        else:
            TaskManager.objects.update(task_id=task.id,
                                       process_id=process_id,
                                       error_flag=False,
                                       error_detail=None,
                                       complete=True)
    else:
        TaskManager.objects.update(task_id=task.id,
                                   process_id=process_id,
                                   error_flag=True,
                                   error_detail=error_blurb,
                                   complete=True)
