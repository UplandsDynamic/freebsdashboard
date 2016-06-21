#!/usr/local/bin/bash

PID_FILE="/var/run/uwsgi_emperor.pid"

## reloads uwsgi_rc.d
/usr/local/bin/uwsgi --reload $PID_FILE;