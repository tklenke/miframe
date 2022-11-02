# Frame Viewer


# SET UP
## Set display resolution
## Load Fallback File



# MAIN LOOP
## Reset timer
## Display current image
## Get Next Image

#


import config as mifcfg
import time
import io
import os
import json

#for html client
import requests


from tkinter import *
from tkinter import ttk

#for photos
#sudo pip install --upgrade pillow  (version 9.2 for dev)
from PIL import Image, ImageTk, ImageFile
from PIL.ExifTags import TAGS
ImageFile.LOAD_TRUNCATED_IMAGES = True

#MiFrame Shared library
from mif import ImageRecord
import mif




#--------functions
        
def ScanFallbackDir(aFBRecs):
    if len(aFBRecs) > 0:
        for val in aFBRecs:
            aFBRecs.pop()
    aFileScans = os.scandir(g_photo_dir)
    for fScan in aFileScans:
        if fScan.is_file():
            (root,ext)=os.path.splitext(fScan.name)
            ext = ext.lower()
            if '.jpg' == ext:
                aFBRecs.append(ImageRecord(fScan.path))   
    return(aFBRecs)            


def CheckPhotoServer():
# Check PhotoServer for next image
## Find PhotoServer on Network
## Request Next Image Meta from PhotoServer
## Request Image from PhotoServer
    #get img record
    image_record_url = "http://10.0.1.33:5000/selectir"
    try:
        r = requests.get(image_record_url)
    except:
        return(None,None)
    if r.status_code != 200:
        return(None,None)

    dDict = r.json()
    imgRec = ImageRecord(dAttr = dDict)

    image_url = f"http://10.0.1.33:5000/{dDict['id']}/img"
    try:
        r = requests.get(image_url)
    except:
        return(None,None)
    if r.status_code != 200:
        return(None,None)
        
    img_data = io.BytesIO(r.content)    
    img = Image.open(img_data)
    
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
    (img, oImgMeta) = CheckPhotoServer()
    if img is not None:
        return (img, oImgMeta)
    #else
    (img, oImgMeta) = CheckFallBackFiles()
    if img is not None:
        return (img, oImgMeta)
    #else
    img = Image.open( g_photo_dir + "1x1white.png")
    
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


#--------main

class Photo(Frame):
    def __init__(self, parent, *args, **kwargs):
        self.parent=parent
        Frame.__init__(self, parent, bg='black')
        self.panel1 = Label(self, image=None, borderwidth=0, highlightthickness=0)
        self.panel1.grid(column=0,row=0)
        self.flip()
    
    def flip(self):

        display_image = GetDisplayReadyImage()

        #show the photo
        self.panel1.config(image=display_image)
        self.panel1.image = display_image  
        self.after(mifcfg.flip_after_millisecs, self.flip)    

class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
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
        Frame.__init__(self, parent, bg='black')
        self.title = ' ' 
        self.calendarLbl = Label(self, text=self.title, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.calendarLbl.grid(column=0,row=0)

class FullscreenWindow:

    def __init__(self):
        self.tk = Tk()
        self.tk.configure(background='black',cursor="none")
        self.topFrame = Frame(self.tk, background = 'black')
        self.topFrame.parent = self
        self.topFrame.grid(sticky=(N,W,E,S))


        #set initial values
        self.state = False
        SetScreenGlobals(self.tk.winfo_screenwidth(), self.tk.winfo_screenheight(),large_text_size,large_text_size)
        print(g_screen_width,g_screen_height,g_max_image_width,g_max_image_height)
     
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
        # Blanks
        self.blankTL = Blank(self.topFrame)
        self.blankTL.grid(column=0,row=0)

        self.blankBR = Blank(self.topFrame)
        self.blankBR.grid(column=4,row=2)


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
        

if __name__ == '__main__':
    
    #set up constants    

    ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
    time_format = 12 # 12 or 24
    date_format = "%b %d, %Y" # check python doc for strftime() for options

    xlarge_text_size = 48
    large_text_size = 24
    medium_text_size = 16
    small_text_size = 8

    g_photo_dir = mifcfg.photo_fallback_path
    g_i_fallback = 0

    #build fallback list
    print("building fallback list")
    g_aFBRecs = []
    g_aFBRecs = ScanFallbackDir(g_aFBRecs)

    #setup windows and begin event loop
    w = FullscreenWindow()
    w.tk.mainloop()




