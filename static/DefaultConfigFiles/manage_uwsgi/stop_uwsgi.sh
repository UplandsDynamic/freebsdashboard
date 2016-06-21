#!/usr/local/bin/bash

PID_FILE="/var/run/uwsgi_emperor.pid"

/usr/local/bin/uwsgi --stop $PID_FILE;
rm -rf $PID_FILE;