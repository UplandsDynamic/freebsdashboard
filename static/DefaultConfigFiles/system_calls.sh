#!/usr/local/bin/bash

if [ $1 == 'take_snapshot' ]
then
     echo taz2015* | /usr/local/bin/sudo -S \
     /sbin/zfs snapshot $2 && \
     echo "Snapshot taken: $2";
elif [ $1 == 'list_snapshots' ]
then
    /sbin/zfs list -H -t snapshot;
elif [ $1 == 'datasets' ]
then
    /sbin/zfs list -H -t filesystem -o name;
elif [ $1 == 'delete_snapshot' ]
then
    /sbin/zfs destroy $2 && \
    echo "Snapshot '$2' destroyed!";
else
    echo "Requested action not available in system_calls.sh";
    exit 1;
fi