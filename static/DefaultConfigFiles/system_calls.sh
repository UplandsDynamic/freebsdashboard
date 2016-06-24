#!/usr/local/bin/bash

if [ $1 == 'take_snapshot' ]
then
     echo taz2015* | /usr/local/bin/sudo -S \
     /sbin/zfs snapshot $2 && \
     echo "Snapshot taken: $2";
elif [ $1 == 'list_snapshots' ]
then
    /sbin/zfs list -H -t snapshot;
elif [ $1 == 'show_filesystems' ]
then
    /sbin/zfs list -H -t filesystem -o name;
elif [ $1 == 'delete_snapshot' ]
then
    /sbin/zfs destroy $2 && \
    echo "Snapshot '$2' destroyed!";
elif [ $1 == 'create_filesystems' ]
then
    echo "Creating $2";
    /sbin/zfs create $2;
else
    echo "Requested action not available in system_calls.sh";
    exit 1;
fi