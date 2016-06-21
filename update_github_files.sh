#!/bin/bash
## updates files to mirror the main dev git repo
chmod 000 .git;
cp -pR /home/dan/Data/zwsDevelopment/PYTHON/PyCharm/PycharmProjects/django/freebsdashboard/* .;
chmod 700 .git;
git add .;
git commit -am 'Update mirrored from development repository'
git push origin master;
echo "Update pushed!"
