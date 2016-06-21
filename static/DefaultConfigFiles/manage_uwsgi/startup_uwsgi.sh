#!/usr/local/bin/bash

PID_FILE="/var/run/uwsgi_emperor.pid"
LOG_FILE="/var/log/uwsgi/uwsgi-emperor.log"
USER="freebsdashboard"
GROUP="www"
VASSAL_DIR="/usr/local/etc/nginx/uwsgi/vassals"

# only run if not already running
if [ -e "$PID_FILE" ]
then
    echo "A uwsgi Emperor is already ruling!"
else
    ## starts the uwsgi Emperor
    echo "The Emperor takes the thone ..."
    /usr/local/bin/uwsgi --emperor $VASSAL_DIR --uid $USER --gid $GROUP \
    --pidfile $PID_FILE --daemonize $LOG_FILE;
fi