#!/usr/local/bin/bash

PID_FILE="/var/run/django_q.pid"
PROJECT_ROOT="/usr/local/freebsdashboard"
VIRTUAL_ENV_DIR="/usr/local/virtual_env"
LOG_DATE=$(date -ju +"%d-%m-%Y.%Z") # u flag sets in UTC
LOG_DIR="/var/log/django_q"

# only run if not already running
if [ -e "$PID_FILE" ]
then
    echo "A django_q cluster is already running!"
else
    ## starts the django_q cluster
    source $VIRTUAL_ENV_DIR/bin/activate
    nohup >> $LOG_DIR/django_q.log.$LOG_DATE $VIRTUAL_ENV_DIR/bin/python $PROJECT_ROOT/manage.py qcluster &
    echo $$ >$PID_FILE
    echo "A django_q cluster is now running ..."
fi