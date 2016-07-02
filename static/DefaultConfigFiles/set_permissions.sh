#!/usr/local/bin/bash

ROOT_DIR=$1;

# create ownership & permissions
chown -R freebsdashboard:www $ROOT_DIR;
chmod -R g+s $ROOT_DIR;
find $ROOT_DIR -type f -exec chmod 400 {} \;
find $ROOT_DIR -type d -exec chmod 750 {} \;
find $ROOT_DIR/web -type f -exec chmod 440 {} \;
find $ROOT_DIR/web -type d -exec chmod 750 {} \;
find $ROOT_DIR/static/DefaultConfigFiles/manage_uwsgi \
-type f -name '*.sh' -exec chmod 0500 {} \;
find $ROOT_DIR/static/DefaultConfigFiles/manage_django_q \
-type f -name '*.sh' -exec chmod 0500 {} \;
chmod 0500 $ROOT_DIR/static/DefaultConfigFiles/system_calls.sh;
chown -R root /usr/local/etc/nginx
chmod 0640 /usr/local/etc/nginx/nginx.conf;
chmod -R 0700 /usr/local/etc/nginx/certificates;
chmod 0550 /usr/local/etc/rc.d/uwsgi;
chown root /usr/local/etc/rc.d/uwsgi;
chmod 0775 /var/log/uwsgi;
chown -R freebsdashboard:wheel /var/log/uwsgi;
chmod 0750 /usr/local/etc/nginx/uwsgi;
chmod 0750 /usr/local/etc/nginx/uwsgi/vassals;
chmod 0777 /sockets;
chown freebsdashboard:www /sockets;
chmod g+s /sockets;
chmod 0550 /usr/local/etc/rc.d/django_q;
chown root /usr/local/etc/rc.d/django_q;
chmod 0700 $ROOT_DIR/static/DefaultConfigFiles/config_django.sh;
# logs
chown freebsdashboard:www /var/log/django_q;
chmod 775 /var/log/django_q;
chmod g+s /var/log/django_q;
umask 111 /var/log/django_q;
chown www:wheel /var/log/django_main;
chmod 775 /var/log/django_main;
chmod g+s /var/log/django_main;
umask 007 /var/log/django_main;

