#!/usr/local/bin/bash
ROOT_DIR='/usr/local/freebsdashboard';
#finish configuring django
source /usr/local/virtual_env/bin/activate;
python $ROOT_DIR/manage.py collectstatic;
python $ROOT_DIR/manage.py makemigrations;
python $ROOT_DIR/manage.py migrate;
python $ROOT_DIR/manage.py makemigrations ZFSAdmin;
python $ROOT_DIR/manage.py migrate ZFSAdmin;
python $ROOT_DIR/manage.py createsuperuser;
chmod 000 /usr/local/freebsdashboard/static/DefaultConfigFiles/config_django.sh;