#!/bin/sh
#
# PROVIDE: django_q
# REQUIRE: DAEMON
# KEYWORD: shutdown

. /etc/rc.subr

name=django_q
rcvar=django_q_enable
wrapper_dir="/usr/local/freebsdashboard/static/DefaultConfigFiles"
command="$wrapper_dir/manage_django_q/startup_django_q.sh"
stop_cmd="$wrapper_dir/manage_django_q/stop_django_q.sh"
restart_cmd="$wrapper_dir/manage_django_q/restart_django_q.sh"
load_rc_config $name
#
# DO NOT CHANGE THESE DEFAULT VALUES HERE
# SET THEM IN THE /etc/rc.conf FILE
#
utility_enable=${django_q_enable-"YES"}
pidfile=${django_q_pidfile-"/var/run/django_q.pid"}
run_rc_command "$@"