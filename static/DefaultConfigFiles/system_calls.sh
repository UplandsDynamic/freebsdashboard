#!/usr/local/bin/bash

FREEBSDASHBOARD_SYSTEM_PASSWORD='default_password';

if [ $1 == 'take_snapshot' ]
then
     echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
     /sbin/zfs snapshot $2;
elif [ $1 == 'list_snapshots' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs list -H -t snapshot;
elif [ $1 == 'show_filesystems' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs list -H -t filesystem -o name;
elif [ $1 == 'delete_snapshot' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs destroy $2;
elif [ $1 == 'clone_snapshot' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs clone $2 $3;
elif [ $1 == 'create_filesystems' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs create $2;
elif [ $1 == 'delete_filesystem' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs destroy -r $2;
else
    echo "Requested action not available in system_calls.sh";
    exit 1;
fi
