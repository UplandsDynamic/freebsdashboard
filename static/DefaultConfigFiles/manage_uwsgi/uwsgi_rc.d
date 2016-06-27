#!/usr/local/bin/bash
#
# PROVIDE: uwsgi
# REQUIRE: DAEMON
# KEYWORD: shutdown
# REQUIRE: LOGIN

. /etc/rc.subr

name=uwsgi
rcvar=uwsgi_enable
wrapper_dir="/usr/local/freebsdashboard/static/DefaultConfigFiles"
command="$wrapper_dir/manage_uwsgi/startup_uwsgi.sh"
extra_commands="kick_vassals"
stop_cmd="$wrapper_dir/manage_uwsgi/stop_uwsgi.sh"
restart_cmd="$wrapper_dir/manage_uwsgi/restart_uwsgi.sh"
kick_vassals_cmd="$wrapper_dir/manage_uwsgi/reload_uwsgi_vassals.sh"
load_rc_config $name
#
# DO NOT CHANGE THESE DEFAULT VALUES HERE
# SET THEM IN THE /etc/rc.conf FILE
#
utility_enable=${uwsgi_enable-"YES"}
pidfile=${uwsgi_pidfile-"/var/run/uwsgi_emperor.pid"}
run_rc_command "$@"