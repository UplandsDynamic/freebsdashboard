#!/usr/local/bin/bash

FREEBSDASHBOARD_SYSTEM_PASSWORD='default_password';

if [ $1 == 'take_snapshot' ]
then
     echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
     /sbin/zfs snapshot $2;
     /usr/local/bin/sudo -K;
elif [ $1 == 'list_snapshots' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs list -H -t snapshot;
    /usr/local/bin/sudo -K;
elif [ $1 == 'show_filesystems' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs list -H -t filesystem -o name;
    /usr/local/bin/sudo -K;
elif  [ $1 == 'get_filesystem_properties' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs get -H -o value $3 $2;
    /usr/local/bin/sudo -K;
elif [ $1 == 'delete_snapshot' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs destroy $2;
    /usr/local/bin/sudo -K;
elif [ $1 == 'clone_snapshot' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs clone $2 $3;
    /usr/local/bin/sudo -K;
elif [ $1 == 'create_filesystems' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs create -o compression=$3 -o sharenfs=$4 -o quota=$5 $2;
    if [ ! -z "$6" ]
    then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs set sharenfs="$6" $2;
    fi
    /usr/local/bin/sudo -K;
elif [ $1 == 'edit_filesystem' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs set sharenfs="$3" $2;
    if [ ! -z "$4" ]
    then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs set sharenfs="$4" $2;
    fi
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs set compression="$5" $2;
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs set quota="$6" $2;



elif [ $1 == 'delete_filesystem' ]
then
    echo $FREEBSDASHBOARD_SYSTEM_PASSWORD | /usr/local/bin/sudo -S \
    /sbin/zfs destroy -r $2;
    /usr/local/bin/sudo -K;
else
    echo "Requested action not available in system_calls.sh";
    exit 1;
fi
