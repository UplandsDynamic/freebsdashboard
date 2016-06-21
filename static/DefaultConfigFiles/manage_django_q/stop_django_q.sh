#!/usr/local/bin/bash

PID_FILE="/var/run/django_q.pid"
PROJECT_ROOT="/usr/local/freebsdashboard"
VIRTUAL_ENV_DIR="/usr/local/virtual_env"
re='^[0-9]+$'  # regex for number test

# stops django_q
source $VIRTUAL_ENV_DIR/bin/activate; \
PID=$($VIRTUAL_ENV_DIR/bin/python $PROJECT_ROOT/manage.py qinfo --ids);
if [[ $PID =~ $re ]]
then
   kill -s SIGTERM $PID && rm -rf $PID_FILE
   echo "Django_q stopped!"
else
    echo "Django_q does not appear to be running!"
fi
