# MiFrame Installation and Set-up

# Service Controls
- Frame
  - `sudo systemctl stop miframe`
  - `sudo systemctl start miframe`
  - `sudo systemctl status miframe`
- Server

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
      and paste following:   
      (note: [USER] is pi, so change if your user is different)
`
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
`
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












