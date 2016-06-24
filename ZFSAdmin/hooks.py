# hooks.py
from .models import TaskManager
import logging

logger = logging.getLogger(__name__)


def update_callback(task):
	# delete the task id from the task manager if no error, else add error flag
	if task.result is True:
		TaskManager.objects.update(task_id=task.id,
		                           process_id='snapshot_updater',
		                           error_flag=False,
		                           complete=True,
		                           error_detail=None)
	else:
		TaskManager.objects.update(task_id=task.id,
		                           process_id='snapshot_updater',
		                           error_flag=True,
		                           complete=True,
		                           error_detail=None)


def delete_callback(task):
	error = ''
	if task.success:
		if task.result:
			for result in task.result:
				if 'error' in result:
					error += '{}, '.format(result.get('error'))
		else:
			error = 'There was a problem running the operation - no result was received.'
		if error:
			TaskManager.objects.update(task_id=task.id,
			                           process_id='snapshot_deleter',
			                           error_flag=True,
			                           error_detail=error.rstrip(', '),
			                           complete=True)
		else:
			TaskManager.objects.update(task_id=task.id,
			                           process_id='snapshot_deleter',
			                           error_flag=False,
			                           error_detail=None,
			                           complete=True)
	else:
		TaskManager.objects.update(task_id=task.id,
		                           process_id='filesystem_creator',
		                           error_flag=True,
		                           error_detail='There was an error initiating the task; snapshots were not deleted!',
		                           complete=True)


def take_snapshots_callback(task):
	error = ''
	if task.success:
		if task.result:
			for result in task.result:
				if 'error' in result:
					error += '{}, '.format(result.get('error'))
		else:
			error = 'There was a problem running the operation - no result was received.'
		if error:
			TaskManager.objects.update(task_id=task.id,
			                           process_id='snapshot_taker',
			                           error_flag=True,
			                           error_detail=error.rstrip(', '),
			                           complete=True)
		else:
			TaskManager.objects.update(task_id=task.id,
			                           process_id='snapshot_taker',
			                           error_flag=False,
			                           error_detail=None,
			                           complete=True)
	else:
		TaskManager.objects.update(task_id=task.id,
		                           process_id='filesystem_creator',
		                           error_flag=True,
		                           error_detail='There was an error initiating the task; snapshots were not created!',
		                           complete=True)


def create_filesystems_callback(task):
	error = ''
	if task.success:
		if task.result:
			for result in task.result:
				if 'error' in result:
					error += '{}, '.format(result.get('error'))
		else:
			error = 'There was a problem running the operation - no result was received.'
		if error:
			TaskManager.objects.update(task_id=task.id,
			                           process_id='filesystem_creator',
			                           error_flag=True,
			                           error_detail=error.rstrip(', '),
			                           complete=True)
		else:
			TaskManager.objects.update(task_id=task.id,
			                           process_id='filesystem_creator',
			                           error_flag=False,
			                           error_detail=None,
			                           complete=True)
	else:
		TaskManager.objects.update(task_id=task.id,
		                           process_id='filesystem_creator',
		                           error_flag=True,
		                           error_detail='There was an error initiating the task; file system was not created!',
		                           complete=True)
