# MiFrame Installation and Set-up

# Non-Technical User (TODO)
## Unit Set-up
1. unbox and plug in
1. on startup Raspbian Desktop wallpaper shows "please wait" until MiFrame starts
    1. MiFrame-frame starts
        1. Checks for config.json, if exists: then goes into normal start up
        1. else: goes into set-up state
    1. MiFrame-Server starts
        1. Checks for config.json if exists: then goes into normal startup
            1. if config.json unit type is frame then server shuts down
            1. else: server starts normal operations
        1. else: server goes into Set-up State
            - Set-up State Flow
                1. default wifi network ssid, password and URL displayed on Frame
                1. user connects to default ssid and navigates to URL
                1. user uses webUI to connect to users preferred network
                1. Server saves connection information to disk
                1. Reboot is scheduled
1. on startup MiFrame shows connection information (URL) to server
    - Welcome to MiFrame.  For photo controls visit http://url


# Technical User

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
- Edit config.py
- Setup services
- Other setup tasks
-- set default wallpaper to MiFrame Startup Image

# Config.json Info
- SSID, password
- Unit type (frame only, server)
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


