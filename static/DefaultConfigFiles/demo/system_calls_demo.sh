#!/usr/local/bin/bash
## DUMMY SYSTEM CALLS
ROOT_DIR='/usr/local/freebsdashboard';

if [ $1 == 'take_snapshot' ]
then
     echo $2 >> $ROOT_DIR/static/DefaultConfigFiles/demo/snapshots_demo.txt && \
     echo "Snapshot taken: $2";
elif [ $1 == 'list_snapshots' ]
then
    cat $ROOT_DIR/static/DefaultConfigFiles/demo/snapshots_demo.txt;
elif [ $1 == 'show_filesystems' ]
then
    cat $ROOT_DIR/static/DefaultConfigFiles/demo/datasets_demo.txt;
elif [ $1 == 'delete_snapshot' ]
then
    sed -i.bak "\#$2#d" $ROOT_DIR/static/DefaultConfigFiles/demo/snapshots_demo.txt && \
    echo "Snapshot '$2' destroyed!";
elif [ $1 == 'create_filesystems' ]
then
    echo "Creating $2";
    echo "$2" >> $ROOT_DIR/static/DefaultConfigFiles/demo/datasets_demo.txt;
else
    echo "Requested action not available in system_calls.sh";
    exit 1;
fi