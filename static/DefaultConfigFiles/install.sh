#!/usr/bin/env bash
## Install script for FreeBSDashboard
## IMPORTANT: Read the README.md first!

# Define FreeBSDashboard root
ROOT_DIR='/usr/local/freebsdashboard';

# create freebsdashboard user
pw user add freebsdashboard -G wheel;
echo 'Enter a password for the freebsdashboard system user - and note it for later!';
passwd freebsdashboard;

# install all pkg's
pkg install git python35 py27-virtualenv mariadb101-server redis nginx;

# install pip3.5
python3.5 -m ensurepip;
pip3.5 install --upgrade pip;

# install & configure uwsgi
pip3.5 install uwsgi;
cp $ROOT_DIR/static/DefaultConfigFiles/manage_uwsgi/uwsgi_rc.d \
/usr/local/etc/rc.d/uwsgi;
echo "uwsgi_enable=\"YES\"" >> /etc/rc.conf;

# install the virtualenv
virtualenv --python=python3.5 /usr/local/virtual_env;

# configure mariadb
echo 'mysql_enable="YES"' >> /etc/rc.conf;
cp /usr/local/share/mysql/my-medium.cnf /usr/local/etc/my.cnf;
service mysql-server start;
/usr/local/bin/mysql_secure_installation;
echo 'Now enter the root mysql password that you just created...';
mysql -u root -p < $ROOT_DIR/static/DefaultConfigFiles/setup.mysql;

# configure redis
echo 'redis_enable="YES"' >> /etc/rc.conf;

# activate and change into the virtualenv
source /usr/local/virtual_env/bin/activate;

# update pip and setup tools
pip install -U setuptools pip;

# install mysqlclient
pip install mysqlclient;

# install django
pip install django;

# install pytz
pip install pytz;

# install django-tables2
pip install django-tables2;

# install redis for django
pip install redis;

# install & configure django-q for async (ZWS fork if/until merged to django_q main)
#pip install django-q;
git clone https://github.com/ZWS2014/django-q.git \
/usr/local/virtual_env/lib/python3.5/site-packages/django_q.git;
cp -R /usr/local/virtual_env/lib/python3.5/site-packages/django_q.git/django_q \
/usr/local/virtual_env/lib/python3.5/site-packages/django_q;
pip install django-picklefield;  # pulled in auto if pip install django_q
pip install future; # pulled in auto if pip install django_q
pip install arrow; # pulled in auto if pip install django_q
pip install blessed; # pulled in auto if pip install django_q

mkdir /var/log/django_q;
cp $ROOT_DIR/static/DefaultConfigFiles/manage_django_q/django_q_rc.d \
/usr/local/etc/rc.d/django_q;
echo "django_q_enable=\"YES\"" >> /etc/rc.conf;

# configure nginx
mv /usr/local/etc/nginx/nginx.conf /usr/local/etc/nginx/nginx.conf_ORIG;
cp $ROOT_DIR/static/DefaultConfigFiles/manage_nginx/nginx.conf \
/usr/local/etc/nginx/nginx.conf;
mkdir -p /usr/local/etc/nginx/uwsgi/vassals;
mv /usr/local/etc/nginx/uwsgi_params /usr/local/etc/nginx/uwsgi_params_ORIG;
cp $ROOT_DIR/static/DefaultConfigFiles/manage_uwsgi/uwsgi_params \
/usr/local/etc/nginx/uwsgi/;
cp $ROOT_DIR/static/DefaultConfigFiles/manage_uwsgi/freebsdashboard_uwsgi.ini \
/usr/local/etc/nginx/uwsgi/vassals/;
echo "nginx_enable=\"YES\"" >> /etc/rc.conf;

# create and install ssl cert
mkdir /usr/local/etc/nginx/certificates;
openssl genrsa -rand -genkey -out /usr/local/etc/nginx/certificates/freebsdashboard.key 4096;
openssl req -new -x509 -days 365 \
-key /usr/local/etc/nginx/certificates/freebsdashboard.key \
-out /usr/local/etc/nginx/certificates/freebsdashboard.crt -sha256;

# create the log directory
mkdir -p /var/log/uwsgi;

# create a dir for the socket
mkdir /sockets;

# create log directory & file
mkdir /var/log/django_main;

# set permissions
chmod +x $ROOT_DIR/static/DefaultConfigFiles/set_permissions.sh;
/usr/local/bin/bash $ROOT_DIR/static/DefaultConfigFiles/set_permissions.sh \
$ROOT_DIR;
chmod 000 $ROOT_DIR/static/DefaultConfigFiles/set_permissions.sh;

# final django configuration
chmod 0740 /usr/local/bin/bash $ROOT_DIR/static/DefaultConfigFiles/config_django.sh;
/usr/local/bin/bash $ROOT_DIR/static/DefaultConfigFiles/config_django.sh;

# start
service nginx start;
service redis start;
service django_q start;
service uwsgi start;

# ensure install and uninstall are not run by accident
chmod 000 $ROOT_DIR/static/DefaultConfigFiles/install.sh;

echo "Do you wish to reboot now? Enter 1 or 2"
select yn in "Reboot now!" "Do not reboot yet!"; do
    case $yn in
        "Reboot now!" ) echo 'Rebooting ...'; reboot; break;;
        "Do not reboot yet!" ) echo "Don't forget to reboot later!"; exit;;
    esac
done
