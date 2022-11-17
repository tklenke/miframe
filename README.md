# MiFrame Installation and Set-up

1. establish network connection
1. user takes USB drive from frame, plugs into their desktop and loads photos into designated directory
and replaces in USB drive frame and reboots 
1. frame starts and looks config.json exists
    - if found continues
    - else scans network server and displays default images or startup screen
1. server starts and looks for config.json
    - if found, follows config.json for startup or shutdown (there's another server online)
    - else, scans network for another server, 
        - if found shutdown
        - else look for photo directory
            - if found, then do new server tasks
            - else, shutdown


# Power User/Developer
- Install Raspbian OS
-- Ensure upto date
--- apt-get update
--- apt-get upgrade
-- Install Dependencies
--- python libraries
---- pip xx
- Clone MiFrame from GitHub
-- git clone
- setup directories
- setup services
- Edit config.py
- Setup services
- Other setup tasks
-- set default wallpaper to MiFrame Startup Image

# Config.json Info
- Unit type (frame only, server)
- server ip
- User definable settings
-- portrait/landscape/both
-- rotation speed
-- categories

wpa_suplicant.conf method
https://www.seeedstudio.com/blog/2021/01/25/three-methods-to-configure-raspberry-pi-wifi/


Empty Simple Flask Project with Notes.

These are my notes on how to get a new project rolling.

###server set up
```
sudo apt-get update
sudo apt-get install python3-pip python3-dev nginx
sudo pip3 install virtualenv
sudo ufw allow 5000
```
remember to close down port 5000 when done debugging
```
sudo ufw delete allow 5000
```

###create a fork and clone the github repository
on github, create a fork for the new project (based on this one, duh) 
then clone that new project into a new directory
##Make a copy of this as a new project
```
mkdir newproj
cd newproj
git clone --bare https://github.com/tklenke/SimplyEmptyFlask.git
cd SimplyEmptyFlask.git
git push --mirror https://github.com/tklenke/new-repository.git
cd ..
rm -rf SimplyEmptyFlask.git
```

In the new project, goto clone with HTTPS section and copy the url 
```
git clone https://github.com/tklenke/new-repository.git
```

###initial set python environment
```
virtualenv myprojectenv
source myprojectenv/bin/activate
pip install gunicorn flask
```

###install any python requirement packages
* see the app for any requirements

###run simpleapp.py with flask
```
cd fwww
export FLASK_APP=simpleapp.py
export FLASK_DEBUG=1
flask run
```

###run simpleapp.py with gunicorn
```
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

###install simpleapp as service
* edit simpleapp.service
  * change user
  * edit paths
```
sudo cp /<path to>/simpleapp/server/simpleapp.service /etc/systemd/system/
sudo systemctl start simpleapp
sudo systemctl enable simpleapp
sudo systemctl status simpleapp
```

###Configure NGinx
```
sudo cp /<path to>/simpleapp/server/simpleapp.nginx /etc/nginx/sites-available/simpleapp
sudo ln -s /etc/nginx/sites-available/simpleapp /etc/nginx/sites-enabled
sudo systemctl restart nginx
sudo ufw allow 'Nginx Full'
```

###Notes
Find gunicorn log in /

###Items to change in new app
* change .gitignore simpleappenv to newappenv
* change simpleapp.py to newapp.py
* change wsgi.py line from simpleapp to newapp
* change simpleapp.server to newapp
* change simpleapp.nginx to newapp
* added server name or ip to newapp.nginx


