# Frame Viewer


# SET UP
## Set display resolution
## Load Fallback File



# MAIN LOOP
## Reset timer
## Display current image
## Get Next Image

#
import configparser
import time
import io
import os
import json
import logging
#for html client
import requests
#for GUI
from tkinter import *
from tkinter import ttk
#for photos
#sudo pip install --upgrade pillow  (version 9.2 for dev)
from PIL import Image, ImageTk, ImageFile
from PIL.ExifTags import TAGS
ImageFile.LOAD_TRUNCATED_IMAGES = True
#MiFrame Shared library
from mif import ImageRecord, CheckPathSlash
import mif
import seeker

#basic setup
logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')

cfg = configparser.ConfigParser()
g_szIniPath = os.getenv('MIFRAME_INI', '/home/admin/projects/miframe/fwww/miframe.ini')
if not os.path.exists(g_szIniPath):
    logging.critical(f"Can't find config file {g_szIniPath}")
    exit()
cfg.read(g_szIniPath)

#--------functions

def SaveIni():
    logging.debug(f"Saving Ini File {g_szIniPath}")
    if not 'VERSION' in cfg:
        cfg['VERSION'] = {}
    cfg['VERSION']['timestamp'] = time.strftime("%a, %d %b %Y %H:%M:%S")
    with open(g_szIniPath, 'w') as configfile:
        cfg.write(configfile)
    g_IniDirty = False
    return()
    

def UpdateCfgWithDict(d):
    if d is None:
        return (False)
    bDirty = False

    for key in d.keys():
        #top level
        if key in cfg:
            #check next level
            for key2 in d[key]:
                if key2 == 'timestamp':
                    continue
                if key2 not in cfg[key] or str(d[key][key2]) != str(cfg[key][key2]):
                    print("1",key,key2)
                    cfg[key][key2] = str(d[key][key2])
                    bDirty = True
        else:
            cfg[key] = {}
            for key2 in d[key]:
                print("1",key,key2)
                cfg[key][key2] = str(d[key][key2])
                bDirty = True
    return(bDirty)

def GetJSONFromServer(szRoute):
    json_url = f"http://{g_ServerIP}:{g_ServerPort}/{szRoute}"
    try:
        r = requests.get(json_url,timeout=2)
    except:
        return(None)
    if r.status_code != 200:
        return(None)
    dDict = r.json()
    return(dDict)
    
def GetImageFromServer(nId):
    image_url = f"http://{g_ServerIP}:{g_ServerPort}/{nId}/img"
    try:
        r = requests.get(image_url,timeout=2)
    except:
        g_bServerLive = False
        return(None)
    if r.status_code != 200:
        logging.info(f"unexpected server response [{r.status_code }]")
        return(None)
        
    img_data = io.BytesIO(r.content)
    return (img_data) 
    
        
def ScanFallbackDir(aFBRecs):
    if len(aFBRecs) > 0:
        for val in aFBRecs:
            aFBRecs.pop()
    aFileScans = os.scandir(g_fallback_dir)
    for fScan in aFileScans:
        if fScan.is_file():
            (root,ext)=os.path.splitext(fScan.name)
            ext = ext.lower()
            if '.jpg' == ext:
                aFBRecs.append(ImageRecord(fScan.path))   
                #this also works to not display logos (png) files as fallback file
    return(aFBRecs)


def CheckPhotoServer():
# Check PhotoServer for next image
## Find PhotoServer on Network
## Request Next Image Meta from PhotoServer
## Request Image from PhotoServer
    #get img record
    # ~ image_record_url = f"http://{g_ServerIP}:{g_ServerPort}/selectir"
    global g_bServerLive
    
    dDict = GetJSONFromServer(f"{g_MachineID}/selectirmid")
    if dDict is None:
        return (None, None)

    imgRec = ImageRecord(dAttr = dDict)

    # ~ image_url = f"http://{g_ServerIP}:{g_ServerPort}/{dDict['id']}/img"
    # ~ try:
        # ~ r = requests.get(image_url,timeout=2)
    # ~ except:
        # ~ g_bServerLive = False
        # ~ return(None,None)
    # ~ if r.status_code != 200:
        # ~ logging.info(f"unexpected server response [{r.status_code }]")
        # ~ return(None,None)
        
    # ~ img_data = io.BytesIO(r.content)    
    img_data = GetImageFromServer(dDict['id'])
    img = Image.open(img_data)
    g_bServerLive = True
    return (img,imgRec)


def CheckFallBackFiles():
# Get Next Image from Fallback File
## Request Next Image Meta from Fallback File
## Request Image from Local Storage
    #Get next file
    global g_i_fallback
    global g_aFBRecs
    if g_i_fallback > len(g_aFBRecs)-1:
        g_i_fallback = 0
        g_aFBRecs = ScanFallbackDir(g_aFBRecs)
    img = Image.open(g_aFBRecs[g_i_fallback].path)
    g_i_fallback += 1
        
    return(img,g_aFBRecs[g_i_fallback-1])

def GetNextImage():
    global g_bServerLive
    (img, oImgMeta) = CheckPhotoServer()
    if img is not None:
        logging.debug(f"server file")
        return (img, oImgMeta)
    #else
    g_bServerLive = False
    (img, oImgMeta) = CheckFallBackFiles()
    if img is not None:
        logging.debug(f"fallback file")
        return (img, oImgMeta)
    #else
    img = Image.open( g_fallback_dir + "MiFrameLogoFull.png")
    
    return(img, None)


def GetDisplayReadyImage():
# Get Next Image
## Check PhotoServer for next image
### Get Next Image from Fallback File
# Rotate and Resize
#TODO check to see if refactoring will reduce memory load from making so many copies of the image
    (imageRaw, oImgRec) = GetNextImage()
    
    #rotate first    
    if oImgRec.orientation in (3,4):
        imageRot = imageRaw.rotate(180,expand=True)
    elif oImgRec.orientation in (5,6):
        imageRot= imageRaw.rotate(270,expand=True)
    elif oImgRec.orientation in (7,8):
        imageRot = imageRaw.rotate(90,expand=True)
    else:
        imageRot = imageRaw
    
    #now find the image aspect ratio and size
    image_s = imageRot.size    
    image_w = image_s[0]
    image_h = image_s[1]

    ratio = float(image_w)/float(image_h)

    if ratio < g_image_ratio:  #height is the constraint (portrait)
        h = int(g_max_image_height)
        w = int(h*ratio)
        photoIsPortrait = True
    else:   #width is the constraint
        w = int(g_max_image_width)
        h = int(w/ratio)
        photoIsPortrait = False

    #then resize
    imageRR = imageRot.resize((w,h),Image.Resampling.LANCZOS)

    img = ImageTk.PhotoImage(imageRR)
    #done with the Pillow image so close
    imageRR.close()
    
    return(img)
    
def SetScreenGlobals(width,height,corner_width,corner_height):
    global g_screen_width
    global g_screen_height
    global g_corner_width
    global g_corner_height
    global g_max_image_width
    global g_max_image_height
    global g_image_ratio
    
    g_screen_width = width
    g_screen_height = height
    g_corner_width = corner_width
    g_corner_height = corner_height
    g_max_image_width = g_screen_width - 3*g_corner_width
    g_max_image_height = g_screen_height - 3*g_corner_height
    g_image_ratio = float(g_max_image_width/g_max_image_height)
    return ()
    
def CheckIni():
    dIni = GetJSONFromServer(f"{g_MachineID}/getini")
    if UpdateCfgWithDict(dIni):
        logging.debug(f"Ini changes. saving")
        SaveIni()
    return ()
        
def CheckFallbackPhotos():
    global g_aFBRecs, g_fallback_dir
    bReloadFallbacks = False
    dFallbacks = GetJSONFromServer(f"{g_MachineID}/fallbacks")
    #returns dict of [ImageRecId]:[filename]
    if dFallbacks:
        #check to see if in list of fallback photos
        logging.debug(f"server returned {len(dFallbacks.keys())} fallbacks")
        for key in dFallbacks.keys():
            bFound = False
            szFileName = dFallbacks[key].split('/')[-1]
            logging.debug(f"checking server fallback {szFileName}")
            for rec in g_aFBRecs:
                szExistFB = rec.path.split('/')[-1]
                if szExistFB == szFileName:
                    bFound = True
            if not bFound:
                #save it
                bReloadFallbacks = True
                logging.debug(f"server fallback {szFileName} not found. Saving...")
                imgdata = GetImageFromServer(key)
                if imgdata is not None:
                    #save to file
                    szSavePath = f"{g_fallback_dir}{szFileName}"
                    logging.debug(f"Saving new fallback to {szSavePath}")
                    with open(szSavePath,'wb') as fp:
                        fp.write(imgdata.getbuffer())
        if bReloadFallbacks:
            g_aFBRecs = []
            CheckFallBackFiles()
    return ()


#--------main

class Photo(Frame):
    def __init__(self, parent, *args, **kwargs):
        logging.debug(f"starting photo")
        self.parent=parent
        Frame.__init__(self, parent, bg='black')
        self.panel1 = Label(self, image=None, textvariable=self.parent.parent.mainMsg, borderwidth=0,\
            highlightthickness=0, font=('Helvetica', large_text_size), fg="white", bg="black",\
            compuund=None)
        self.panel1.grid(column=0,row=0, sticky=(S))
        # ~ self.flip()
        self.after(2000, self.flip)
    
    def flip(self):
        # ~ if self.parent.parent.mainMsg.get() == '':
        logging.debug(f"image[{self.parent.parent.mainMsg.get()}]")
        display_image = GetDisplayReadyImage()

        #show the photo
        self.panel1.config(image=display_image)
        self.panel1.image = display_image
        # ~ else:
            # ~ logging.debug(f"text[{self.parent.parent.mainMsg.get()}]")
            # ~ self.panel1.config(image=None)
            
        self.after(cfg.getint('FRAME','flip_after_millisecs'), self.flip)
        

class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        logging.debug(f"starting clock")
        Frame.__init__(self, parent, bg='black')
        self.columnconfigure(0)
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.timeLbl.grid(column=0,row=0,sticky=(E))
        # initialize day of week
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.dayOWLbl.grid(column=1,row=0,sticky=(E))
        # initialize date label
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.dateLbl.grid(column=2,row=0,sticky=(E))
        self.tick()

    def tick(self):
        if time_format == 12:
            time2 = time.strftime('%I:%M %p') #hour in 12h format
        else:
            time2 = time.strftime('%H:%M') #hour in 24h format

        day_of_week2 = time.strftime('%A')
        date2 = time.strftime(date_format)
        # if time string has changed, update it
        if time2 != self.time1:
            self.time1 = time2
            self.timeLbl.config(text=time2)
        if day_of_week2 != self.day_of_week1:
            self.day_of_week1 = day_of_week2
            self.dayOWLbl.config(text=day_of_week2)
        if date2 != self.date1:
            self.date1 = date2
            self.dateLbl.config(text=date2)
        # calls itself every 200 milliseconds
        # to update the time display as needed
        # could use >200 ms, but display gets jerky
        self.timeLbl.after(200, self.tick)
        

class Blank(Frame):
    def __init__(self, parent, *args, **kwargs):
        logging.debug(f"starting blank")
        Frame.__init__(self, parent, bg='black')
        self.title = ' ' 
        self.calendarLbl = Label(self, text=self.title, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.calendarLbl.grid(column=0,row=0)

class SystemMsg(Frame):
    def __init__(self, parent, *args, **kwargs):
        logging.debug(f"starting system msg")
        Frame.__init__(self, parent, bg='black')
        self.parent=parent
        self.textmsgLbl = Label(self, textvariable=self.parent.parent.sysMsg, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.textmsgLbl.grid(column=0,row=0,sticky=(S))

class FullscreenWindow:

    def __init__(self):
        logging.debug(f"starting fullscreenwindow")
        global g_bServerLive, g_ServerIP, g_ServerPort
        self.tk = Tk()
        self.tk.configure(background='black',cursor="none")
        self.topFrame = Frame(self.tk, background = 'black')
        self.topFrame.parent = self
        self.topFrame.grid(sticky=(N,W,E,S))

        #set initial values
        self.state = False
        SetScreenGlobals(self.tk.winfo_screenwidth(), self.tk.winfo_screenheight(),large_text_size,large_text_size)
        logging.debug(f"Screen Dims: {g_screen_width,g_screen_height,g_max_image_width,g_max_image_height}")

        #set up runner and initial message
        self.sRunner = 'init'
        self.nRunnerTick = 0
        self.runner()

        #pad out screen
        self.topFrame.columnconfigure(0,minsize = g_corner_width)
        self.topFrame.columnconfigure(1,minsize = g_max_image_width)
        self.topFrame.columnconfigure(2,minsize = g_corner_width)
        
        self.topFrame.rowconfigure(0,minsize = g_corner_width)
        self.topFrame.rowconfigure(1,minsize = g_max_image_height)
        self.topFrame.rowconfigure(2,minsize = g_corner_width)
        
        
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.grid(column=1,row=2,sticky=(E))
        # Photo
        self.photo = Photo(self.topFrame)
        self.photo.grid(column=1,row=1,columnspan=2)
        # Blank
        self.blankTL = Blank(self.topFrame)
        self.blankTL.grid(column=0,row=0)
        # Message
        self.sysmsg = SystemMsg(self.topFrame)
        self.sysmsg.grid(column=1,row=0,columnspan=2)

        self.toggle_fullscreen()

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        exit()
        return "break"

    def runner(self):
        global g_bServerLive, g_ServerIP, g_ServerPort, g_IniDirty, g_szIniPath, g_runner_mx_tick
        self.nRunnerTick += 1
        logging.debug(f"runner status: [{self.nRunnerTick}]{self.sRunner} server live {g_bServerLive}")
        if self.sRunner == 'init':
            logging.debug(f"init")
            self.mainMsg = StringVar()
            self.mainMsg.set('Starting MiFrame...')
            self.sysMsg = StringVar()
            self.sysMsg.set('Starting MiFrame...')            
            self.sRunner = 'server-unknown'
            self.tk.after(5000, self.runner)
            return()
        elif self.sRunner == 'server-unknown':
            logging.debug(f"server-unknown")
            self.sysMsg.set(f"Checking for server {g_ServerIP}")
            self.sRunner = 'server-check'
            self.tk.after(100, self.runner)
            return()
        elif self.sRunner == 'server-check':
            logging.debug(f"server-check")
            if seeker.CheckIPForMiFrameServer(g_ServerIP,g_ServerPort):
                #it is live
                g_bServerLive = True
                self.mainMsg.set('')
                # ~ self.mainMsg = None
                self.sRunner = 'nominal'
                self.tk.after(100, self.runner)
                return()                
            else:
                g_bServerLive = False
                self.mainMsg.set('')
                self.sysMsg.set(f"Server {g_ServerIP} not found. Searching Network...")
                self.sRunner = 'server-search'
                self.tk.after(100, self.runner)
                return()
        elif self.sRunner == 'server-search':
            logging.debug(f"server-search")            
            szIP = seeker.ScanNetworkForMiFrameServer(g_ServerPort)
            if szIP is None:
                g_bServerLive = False
                self.sysMsg.set(f"No live server on network")
            else:
                g_bServerLive = True
                if szIP != g_ServerIP:
                    g_ServerIP = szIP
                    cfg['NETWORK']['server_ip'] = szIP
                    g_IniDirty = True
                # ~ self.mainMsg = None
                self.mainMsg.set('')
            #give nominal a chance to run
            self.sRunner = 'nominal'
            self.tk.after(100, self.runner)
            return()
        elif self.sRunner == 'nominal':
            logging.debug(f"nominal")
            if not g_bServerLive:
                #server is offline so start the search
                if self.mainMsg is None:
                    self.mainMsg = StringVar()
                self.sysMsg.set(f"Server {g_ServerIP} offline")
                self.sRunner = 'server-check'
                self.tk.after(100, self.runner)
                return()                
                
            #do maintenance tasks every 10 minutes
            if self.nRunnerTick > g_runner_mx_tick:
                self.sysMsg.set(f"Running Maintenance Tasks")             
                self.nRunnerTick = 0
                #check server for ini changes
                logging.debug(f"doing mx tasks")
                CheckIni()
                #check server for list of favorites
                CheckFallbackPhotos()
            
            #all is truly nominal so check again in a second
            self.mainMsg.set('')
            self.sysMsg.set('')
            self.sRunner = 'nominal'
            self.tk.after(1000, self.runner)
            return()                

        #else
        logging.error(f"runner in unexpected state {self.sRunner}")
        self.tk.after(1000, self.runner)
        

if __name__ == '__main__':
    if cfg.getboolean('LEVEL','debug'):
        logging.getLogger().setLevel(logging.DEBUG)
        g_runner_mx_tick = 6
    else:
        logging.getLogger().setLevel(logging.ERROR)
        g_runner_mx_tick = 600
    #set up constants    
    ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
    time_format = 12 # 12 or 24
    date_format = "%b %d, %Y" # check python doc for strftime() for options

    xlarge_text_size = 48
    large_text_size = 24
    medium_text_size = 16
    small_text_size = 8

    g_fallback_dir = CheckPathSlash(cfg['PATHS']['frame_fallback_path'])
    g_i_fallback = 0
    
    g_ServerIP = cfg['NETWORK']['server_ip']
    g_ServerPort = cfg.getint('NETWORK','server_port')
    g_bServerLive = False
    
    g_MachineID = mif.GetMachineId()
    g_IniDirty = False    

    #build fallback list
    logging.debug(f"building fallback list")
    g_aFBRecs = []
    g_aFBRecs = ScanFallbackDir(g_aFBRecs)
    
    #setup windows and begin event loop
    w = FullscreenWindow()
    logging.debug(f"Done init")
    w.tk.mainloop()




