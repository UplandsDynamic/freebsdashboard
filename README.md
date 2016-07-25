FreeBSDashboard
---------------

###UPDATE 25 JULY 2016

Development suspended due to lack of interest.

If you found this useful and would like to see development resumed in future,
please get in touch, either through github or email: dan@aninstanceofme.com

#####VERSION

ALPHA 2.5, PROTOTYPE DEMO. NOT FOR PRODUCTION USE!

This version just has a ZFS Administration section, with basic functionality.

DO NOT INSTALL AND TEST THIS ON A SYSTEM UPON WHICH THERE IS DATA THAT
MEANS ANYTHING TO YOU! THIS IS A PROTOTYPE - DATA LOSS MAY BE INCURRED, AND
YOUR SYSTEM MAY BE DESTROYED - OR WORSE - TRANSFORMED INTO A BLUEBERRY CRUMBLE.

DESCRIPTION
-----------

FreeBSDashboard is a web-gui dashboard to administer FreeBSD systems.

It is currently built and tested for use with FreeBSD version 10.x.

The application uses Python 3.5 (in a virtual environment), and is built using
the Python Django framework and jQuery.

The application calls system shellscripts written in Bash. It uses MariaDB and Redis to
store application and transitory informational data. 

However, it is important to note that, by design, any changes to configuration files 
or system data are applied directly to the files/data on the system. 

Configurations are NOT stored in the application database, which means manual changes
to system configuration files would not be overwritten by the application (and vice-versa).

DEMO
-----------

To test the gui dashboard without installation, try the live prototype demo at:

https://freebsdashboard.aninstanceofme.com:8443

POINTS OF CONTACT
-----------------

GitHub: https://github.com/ZWS2014/freebsdashboard

IRC: #FreeBSDashboard channel on FreeNode network

Email: dan@aninstanceofme.com

Twitter: @aninstanceofme

HOW TO INSTALL
-------------------

Unpack the freebsdashboard project to:

    /usr/local/freebsdashboard

The install script will install a python3.5 virtual environment to:

    /usr/local/virtual_env

It's advisable to update the system and packages/ports prior to installation.

If installing by running the install.sh script as-is, it's advisable to install
this on a clean, fresh  FreeBSD install.

If installing on an existing system, it's recommended to read and amend the
install.sh script according to your current system setup
(i.e. taking into account packages that you may already have installed,
such as Nginx, Redis, or a MySQL server).

Bash needs to be installed prior to running this script (pkg install bash),
and /usr/local/bin/bash needs to be executable by the "wheel" group.

The install  script needs to be run with bash, as root, like so:

    cd /usr/local/freebsdashboard/static/DefaultConfigFiles
    sudo bash
    chmod 0700 install.sh
    ./install.sh

INSTALL ASSUMPTIONS
-------------------

The install.sh script as provided makes the following assumptions, in addition to
those referenced above:

a) Sudo is already installed on the system; the 'wheel' group exists; and
users who're members of the wheel group are able to run commands as root with sudo.

b) ZFS is installed and enabled on your system.

c) For this DEMO version, ensure that there is at least one zpool created on your
system prior to installation. Ultimately, it's intended that this utility
will offer the option to create new zpools, however this has not yet been
implemented.

DEPENDENCIES
------------

All required FreeBSD package dependencies (other than sudo and bash) are installed
by the install.sh script.

Likewise, python dependences are installed by the install.sh script, into the
virtual environment, using pip.

FYI, FreeBSD package dependencies are:

git, python35, py27-virtualenv, mariadb101-server, redis, nginx

Python3.5 system dependencies are:

pip, uwsgi

The rest of the python dependencies are installed and contained within the virtual
environment (read through install.sh if you want to see what's installed).

PRE INSTALL
-------------------

BEFORE installation, you need to take the following steps:

Choose a password for the mysql database and edit the following setup.mysql file, 
replacing "tester_password_2016" with your chosen password:

    /usr/local/freebsdashboard/static/DefaultConfigFiles/setup.mysql

Add the mysql database password to the settings.py file as follows:

Open the following file in your favourite text editor:

    /usr/local/freebsdashboard/freebsdashboard/settings.py

Find the DATABASES section in the above file and change the password to match 
that which you just defined in the setup.mysql file, for example:

    'PASSWORD': 'MyNewDatabasePassword',

POST INSTALL
-------------------

YOU WILL NEED TO REBOOT YOUR SYSTEM ONCE THE INSTALL SCRIPT HAS COMPLETED.

Following installation, you will need edit the system_calls.sh file and 
replace the freebsdashboard user password (default_password) with the one 
that you set during the install process.

So, open the following file in a text editor

    /usr/local/freebsdashoard/static/DefaultConfigFiles/system_calls.sh

and edit this appropriately:

    FREEBSDASHBOARD_SYSTEM_PASSWORD='default_password'

Security of the system may be further enhanced thus:

a) If you're looking to lock-down the permissions further,
edit /etc/sudoers (visudo) so as to restrict the user
'freebsdashboard' from running any script with sudo other than the
/usr/local/freebsdashboard/static/DefaultConfigFiles/system_calls.sh file.

b) Access to the web-gui may be restricted to IP, by editing the Nginx
config file at:

    /usr/local/etc/nginx.conf

Uncomment the following lines in the http block and replace the IP (or IP range)
with that to which you'd like to allow access:

    allow 192.168.1.0/24;
    deny all;
    
USAGE
-----

##### Access the web-gui dashboard

To access the web-gui dashboard, visit the following URL, replacing SERVER_IP 
with the IP of your server. 

Note that the demo installation creates a self-signed certificate, so although the encryption 
itself is secure enough, the verified certificate signing element is clearly missing 
(hence the browser warnings):

https://SERVER_IP:8443

Login using the username and password that you defined during the final step
of the install process (if using the install.sh script).

If you've forgotten your login credentials and need to create a new superuser,
run the following commands from your system's CLI:

    sudo bash;
    source /usr/local/virtual_env/bin/activate;
    python /usr/local/freebsdashboard/manage.py createsuperuser
    
If you should ever need to access the databases directly, or do any user 
administration, the login to Django's inbuilt admin section is at:

https://SERVER_IP:8443/admin

UPDATES & VERSION UPGRADES
--------------------------

In the event that this is application reaches a full release version, it would be 
ported and packaged for FreeBSD and updates would therefore occur in the usual way.

In the meantime, a dedicated upgrade script should hopefully be available come the 
first Beta release.

To update whilst this is an Alpha release (which is intended as a prototype, for 
demo purposes only), fetch the updates from master branch of the github repo at:

https://github.com/ZWS2014/freebsdashboard.git

To fetch the latest commits from master branch and overwrite the installed version 
*without retaining any local changes*, use the following git commands:

    git fetch --all
	git reset --hard origin/master

After doing this, you may need to run the following script to reset permissions:

    /usr/local/freebsdashboard/static/DefaultConfigFiles/set_permissions.sh

USEFUL COMMANDS
-------------------

To control the UWSGI server (this is required to be running):

    sudo service uwsgi start|stop|restart

To control the django_q async task handler (this is required to be running):

    sudo service django_q start|stop|restart

To control the nginx web server (this is required to be running):

    sudo service nginx start|stop|restart

LOGS
-------------------

Log locations are:

    UWSGI: /var/log/uwsgi/freebsdashboard.log | /var/log/uwsgi/uwsgi-emperor.log
    NGINX: /var/log/nginx-error.log | /var/log/nginx-access.log
    DJANGO_Q: /var/log/django_q/django_q.log.DATE_PROCESS_BEGAN

-------------------
