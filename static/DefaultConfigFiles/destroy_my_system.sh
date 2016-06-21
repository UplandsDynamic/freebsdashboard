#!/usr/bin/env bash
## Uninstall script for FreeBSDashboard
##
## RUNNING THIS SCRIPT MAY DESTROY YOUR SYSTEM.
##
## This uninstalls everything installed by the install script,
## including NGINX!
## USE WITH EXTREME CAUTION!

# stop services
service uwsgi stop;
service django_q stop;
service nginx stop;
service redis stop;

# ensure processes have stopped & remove pid files
killall uwsgi
rm -rf /var/run/django_q.pid
rm -rf /var/run/uwsgi_emperor.pid
rm -rf /var/run/uwsgi_freebsdashboard.pid

# uninstall git
pkg remove git;

# uninstall redis
pkg remove redis;
sed -i.bak '/redis_enable=\"YES\"/d' /etc/rc.conf;

# uninstall the virtualenv

rm -rf /usr/local/virtual_env;
pkg remove py27-virtualenv;

# uninstall uwsgi
pip3.5 uninstall uwsgi;
rm -rf /usr/local/etc/rc.d/uwsgi;
sed -i.bak '/uwsgi_enable=\"YES\"/d' /etc/rc.conf;
# rm -rf /var/log/uwsgi;  # delete logs?
rm -rf /sockets;

# uninstall django_q
rm -rf /usr/local/etc/rc.d/django_q;
sed -i.bak '/django_q_enable=\"YES\"/d' /etc/rc.conf;
# rm -rf /var/log/django_q;  # delete logs?

# uninstall python3.5
pkg remove python35;
rm -rf /usr/local/lib/python3.5;

# uninstall nginx
pkg remove nginx;
rm -rf /usr/local/etc/nginx;
sed -i.bak '/nginx_enable=\"YES\"/d' /etc/rc.conf;

# uninstall mariadb
pkg remove mariadb101-server;
sed -i.bak '/mysql_enable="YES"/d' /etc/rc.conf;
killall -u mysql;
# Uncomment below lines if you REALLY want to remove mysql & ALL databases!
#rm -rf /usr/local/etc/my.cnf;
#rm -rf /var/db/mysql;

# remove freebsdashboard user
pw user del freebsdashboard;