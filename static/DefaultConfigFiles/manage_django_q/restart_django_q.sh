#!/usr/local/bin/bash

STOP_SCRIPT="/usr/local/freebsdashboard/static/DefaultConfigFiles/manage_django_q/stop_django_q.sh"
START_SCRIPT="/usr/local/freebsdashboard/static/DefaultConfigFiles/manage_django_q/startup_django_q.sh";
PID_FILE="/var/run/django_q.pid"

/usr/local/bin/bash $STOP_SCRIPT;
while [ ! -e "$PID_FILE" ]; do
             /usr/local/bin/bash $START_SCRIPT
         done
