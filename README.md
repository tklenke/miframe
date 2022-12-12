# MiFrame

Welcome to MiFrame, a client-server architecture for displaying your photo library.
Hardware requirements are a Raspberry Pi with an external drive connected to a display.  
System supports multiple MiFrames being served photos from a single MiFrame-Server.  
Use your phone or other network device with a web browser to Liked, Blocked, or Rotated
photos from your library.    

# Service Controls
- Frame
  - `sudo systemctl stop miframe`
  - `sudo systemctl start miframe`
  - `sudo systemctl status miframe`
- Server

# MiFrame Installation and Set-up

# Power User/Developer
1. Install Raspbian OS
  - Ensure upto date
    - apt-get update
    - apt-get upgrade
  - Install Dependencies
    - python libraries
    - pip xx
1. Install MiFrame 
  - Clone MiFrame from GitHub
    `git clone https://github.com/tklenke/miframe --depth 1 --branch=master ~/miframe`
  - Edit config file
    `mv ~/miframe/fwww/miframe.ini ~`
      - ensure [LEVEL] debug = False
      - edit [PATHS] photo_fallback_path = /home/[USER]/Pictures/  
          ensure paths end in '/' other paths are for server so don't change
1. Setup services
  - create frame service via:
    `sudo systemctl --force --full edit miframe.service`  
    and paste following (note: [USER] is pi, so change if your user is different):
    
1. Alternate for running on linux or windows standalone
  - set environment variable MIFRAME_INI to path to miframe.ini file
    - Linux `set MIFRAME_INI=\home\user\miframe.ini`
    - Windows PS `$env:MIFRAME_INI = 'c:\users\user\documents\miframe\miframe.ini`

```
[Unit]
Description=MiFrame Client
After=network.target multi-user.target graphical.target

[Service]
user=pi
Environment="DISPLAY=:0"
Environment="MIFRAME_INI=/home/pi/miframe.ini"
Environment="XAUTHORITY=/home/pi/.Xauthority"
WorkingDirectory=/home/pi/miframe/fwww/src    
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python /home/pi/miframe/fwww/src/frame.py

[Install]
WantedBy=graphical.target
```
  - Save it and reload all Systemd services via:
    `sudo systemctl daemon-reload`
  - Enable autostart on boot of your new service via:
    `sudo systemctl enable miframe.service`
  - View status of service via:
    `sudo systemctl status miframe.service`
  - View logs via:
    `journalctl -u miframe.service`

  - Other setup tasks
    - set default wallpaper to MiFrame Startup Image
    
    
# MiFrame-Server Install
1. Install MiFrame as noted above
1. Set-up MiFrameServer
- install UFW and configure  
```
sudo apt-get install ufw
sudo ufw allow 80
```
- Set-up Service
  - create frame service via:
    `sudo systemctl --force --full edit miframeserver.service`  
    and paste following (note: [USER] is pi, so change if your user is different):

```
[Unit]
Description=MiFrame Server
After=network.target

[Service]
user=pi
Environment="MIFRAME_INI=/home/pi/miframe.ini"
WorkingDirectory=/home/pi/miframe/fwww    
ExecStartPre=/bin/sleep 7
ExecStart=/usr/bin/flask run --host=0.0.0.0 --port=5000

[Install]
WantedBy=graphical.target
```
  - Save it and reload all Systemd services via:
    `sudo systemctl daemon-reload`
  - Enable autostart on boot of your new service via:
    `sudo systemctl enable miframeserver.service`
  - View status of service via:
    `sudo systemctl status miframeserver.service`
  - View logs via:
    `journalctl -u miframeserver.service`


# Aspirational Flow
1. establish network connection
1. user takes USB drive from frame, plugs into their desktop and loads photos into designated directory
and replaces in USB drive frame and reboots 
1. frame starts and looks config exists
    - if found continues
    - else scans network server and displays default images or startup screen
1. server starts and looks for config
    - if found, follows config for startup or shutdown (there's another server online)
    - else, scans network for another server, 
        - if found shutdown
        - else look for photo directory
            - if found, then do new server tasks
            - else, shutdown












