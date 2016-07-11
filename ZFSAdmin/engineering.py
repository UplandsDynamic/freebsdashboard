import subprocess
from .models import *
import re
from datetime import datetime
from django.utils import timezone
from django.conf import settings
import pytz
import logging

# from django.db import IntegrityError

# system operations

logger = logging.getLogger(__name__)


def update_zfs_data():
    process_result = []
    # RETRIEVES THE LATEST ZFS SNAPSHOT DATA & UPDATES MODEL
    snapshots = []
    snapshot_result = subprocess.run(
        ['{}static/DefaultConfigFiles/{}'.format(settings.PROJECT_ROOT, settings.SYSTEM_CALL_SCRIPT_NAME),
         'list_snapshots'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if settings.DEBUG:
        logger.error('STDOUT: {}'.format(snapshot_result.stdout))
    if not snapshot_result:
        process_result.append({'error': 'No snapshots were obtained; '
                                        'there was an error initialising the process'})
    if snapshot_result.stderr and snapshot_result.stderr != 'Password:':
        # Note: disregard "Password:" as an error - it's simply  passed to stderr during sudo -S process.
        process_result.append({'error': snapshot_result.stderr})
    if snapshot_result.stdout:
        snapshot_data = process_data(stdout_str=snapshot_result.stdout, data_type='snapshots')
        if snapshot_data:
            for snapshot in snapshot_data:
                snapshots.append({'task': 'snapshots_task',
                                  'datetime_created': snapshot.get('datetime'),
                                  'dataset': snapshot.get('dataset'),
                                  'retention': snapshot.get('longevity'),
                                  'name': snapshot.get('name')})
            process_result.append(snapshots)
    # RETRIEVES LATEST ZFS FILESYSTEM NAMES DATA
    properties = ['compression', 'compressratio', 'mountpoint', 'sharenfs', 'sharesmb']
    datasets = {}
    filesystem_result = subprocess.run(
        ['{}static/DefaultConfigFiles/{}'.format(settings.PROJECT_ROOT, settings.SYSTEM_CALL_SCRIPT_NAME),
         'show_filesystems'],
        stdout=subprocess.PIPE, universal_newlines=True)
    if settings.DEBUG:
        logger.error('STDOUT: {}'.format(filesystem_result.stdout))
    if not filesystem_result:
        process_result.append({'error': 'No datasets were obtained; '
                                        'there was an error initialising the process'})
    # Note: disregard "Password:" as an error - it's simply  passed to stderr during sudo -S process.
    if filesystem_result.stderr and filesystem_result.stderr != 'Password:':
        process_result.append({'error': filesystem_result.stderr})
    if filesystem_result.stdout:
        filesystems = process_data(stdout_str=filesystem_result.stdout, data_type='filesystems')
        if filesystems:
            for fs in filesystems:
                property_dict = {}
                for p in properties:
                    properties_result = subprocess.run(
                        ['{}static/DefaultConfigFiles/{}'.format(settings.PROJECT_ROOT,
                                                                 settings.SYSTEM_CALL_SCRIPT_NAME),
                         'get_filesystem_properties', fs.get('filesystem'), p], stdout=subprocess.PIPE,
                        universal_newlines=True)
                    if properties_result.stdout:
                        property_dict[p] = process_data(stdout_str=properties_result.stdout, data_type='properties')
                datasets[fs.get('filesystem')] = property_dict
        process_result.append(datasets)
        logger.error('>>>>>>>' + str(datasets))
    return process_result


def create_filesystems(data=None):
    # CREATES ZFS FILESYSTEMS
    process_result = []
    if data:
        for d in data:
            if d.get('filesystem'):
                # process submitted formset data
                processed_data = process_data(submitted_data=d, data_type="filesystems")
                result = subprocess.run(
                    ['{}static/DefaultConfigFiles/{}'.format(settings.PROJECT_ROOT, settings.SYSTEM_CALL_SCRIPT_NAME),
                     'create_filesystems',
                     processed_data.get('name'),
                     processed_data.get('compression'),
                     processed_data.get('sharenfs'),
                     processed_data.get('quota')],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if settings.DEBUG:
                    logger.error('STDOUT: {}'.format(result.stdout))
                    logger.error('STDERR: {}'.format(result.stderr))
                if not result:
                    process_result.append({'error': 'No filesystems were created; '
                                                    'there was an error initialising the process'})
                elif result.stderr:
                    process_result.append({'error': result.stderr})
                else:
                    process_result.append({'success': result.stdout})
    else:
        process_result.append({'error': 'No file system names were passed for creating!'})
    return process_result


def delete_filesystem(fs_names=None):
    # DELETES FILESYSTEM OF PASSED IN NAME
    process_result = []
    if fs_names:
        for fs in fs_names:
            result = subprocess.run(
                ['{}static/DefaultConfigFiles/{}'.format(settings.PROJECT_ROOT, settings.SYSTEM_CALL_SCRIPT_NAME),
                 'delete_filesystem', fs],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.stderr:
                process_result.append({'error': result.stderr})
            else:
                process_result.append({'success': result.stdout})
    else:
        process_result.append({'error': 'No file systems  were passed for deletion!'})
    return process_result


def take_snapshots(datasets=None):
    # TAKES SNAPSHOTS OF PASSED IN DATASETS LIST
    process_result = []
    if datasets:
        for dataset in datasets:
            snapshot_name = "{}@manual-{}-{}mins".format(
                dataset,
                datetime.strftime(timezone.now(), '%d-%m-%Y.%H:%M:%S.%Z'),
                0)  # for now, give manual snapshots longevity of 0 (infinite)
            # take snapshot of dataset
            result = subprocess.run(
                ['{}static/DefaultConfigFiles/{}'.format(settings.PROJECT_ROOT, settings.SYSTEM_CALL_SCRIPT_NAME),
                 'take_snapshot', snapshot_name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.stderr:
                process_result.append({'error': result.stderr})
            else:
                process_result.append({'success': result.stdout})
    else:
        process_result.append({'error': 'No datasets were passed for snapshotting!'})
    return process_result


def delete_snapshots(datasets=None):
    # DELETES SNAPSHOTS OF PASSED IN DATASET LIST
    process_result = []
    if datasets:
        for snapshot in datasets:
            result = subprocess.run(
                ['{}static/DefaultConfigFiles/{}'.format(settings.PROJECT_ROOT, settings.SYSTEM_CALL_SCRIPT_NAME),
                 'delete_snapshot', snapshot],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.stderr:
                process_result.append({'error': result.stderr})
            else:
                process_result.append({'success': result.stdout})
    else:
        process_result.append({'error': 'No datasets were passed for deletion!'})
    return process_result


def clone_snapshots(snapshots=None):
    # TAKES SNAPSHOTS OF PASSED IN DATASETS LIST
    process_result = []
    if snapshots:
        for snapshot_name in snapshots:
            clone_name = "{}/clone-{}".format(
                process_data(stdout_str=snapshot_name, data_type='snapshots')[0].get('dataset'),
                datetime.strftime(timezone.now(), '%d-%m-%Y.%H:%M:%S.%Z'))
            # take snapshot of dataset
            result = subprocess.run(
                ['{}static/DefaultConfigFiles/{}'.format(settings.PROJECT_ROOT, settings.SYSTEM_CALL_SCRIPT_NAME),
                 'clone_snapshot', snapshot_name, clone_name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.stderr:
                process_result.append({'error': result.stderr})
            else:
                process_result.append({'success': result.stdout})
    else:
        process_result.append({'error': 'No datasets were passed for cloning!'})
    return process_result


# helper functions

''' Debug dev note: strptime = str to datetime, strftime = datetime to string '''


def process_data(stdout_str=None, submitted_data=None, data_type=None):
    # parses the STDOUT strings, extracts the relevant data & returns list of dicts
    return_data = []
    if data_type == 'snapshots':
        snapshot_list = stdout_str.split('\n')
        if snapshot_list:
            for snapshot in filter(None, snapshot_list):  # filter to clear emtpy elements
                data = {}
                try:
                    match = re.match(
                        r"^(?P<dataset>.*(?=@))@(?P<type>[A-Za-z]*(?=-))-(?P<datetime>.*(?=-.*mins))-(?P<longevity>.*("
                        r"?=mins)).*$",
                        snapshot)
                    # format to units required for model & return in dict with keys matching model fields
                    data['datetime'] = pytz.utc.localize(datetime.strptime(
                        match.group('datetime'), '%d-%m-%Y.%H:%M:%S.%Z'))  # datetime obj, made aware (localized to
                    # UTC)
                    data['dataset'] = match.group('dataset')
                    data['longevity'] = match.group('longevity')
                    data['name'] = '{}@{}-{}-{}mins'.format(match.group('dataset'),
                                                            match.group('type'),
                                                            match.group('datetime'),
                                                            match.group('longevity'))
                    return_data.append(data)
                except AttributeError as e:
                    if settings.DEBUG:
                        logger.error('A data parsing error occurred: {}'.format(e))
    elif data_type == 'filesystems':
        if stdout_str:
            filesystem_list = stdout_str.split('\n')
            for key, filesystem in enumerate(filter(None, filesystem_list)):
                return_data.append({'filesystem_id': key, 'filesystem': filesystem,
                                    'zpool': filesystem.split('/')[0]})
        elif submitted_data:
            return {'name': '{}/{}'.format(submitted_data['datasets'],
                                           # filesystem filtered to remove leading & trailing slashes, & anything not: A-Za-z0-9-_/
                                           re.sub(r'[^A-Za-z0-9-_/]', '',
                                                  submitted_data.get('filesystem')).strip('/')),
                    'compression': submitted_data.get('compression') if submitted_data.get('compression') else 'off',
                    'sharenfs': 'on' if submitted_data.get('sharenfs') else 'off',
                    'quota': '{}G'.format(submitted_data.get('quota')) if submitted_data.get('quota') else 'none'}
    elif data_type == 'properties':
        # TODO: any additional filtering?
        return stdout_str.strip('\n')
    return return_data if return_data else None
