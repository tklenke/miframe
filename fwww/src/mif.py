#################################
##  Project Utilities and Image Record Object
##  class ImageRecord
##  LoadIRcsv
##  SaveIRcsv
##  GetStandardDays
##  DictInc
##  GetMachineId
##  CheckPathSlash
##  BackupFile
##################################
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS
import json
import csv
import os
import shutil
import logging
import datetime
import uuid

TS_EPOCH_DAY = 631170000.0
PILLOW_IMAGE_BUF_SZ = 24000000

# ~ #image record
# ~ IR_PATH = 0
# ~ #path
# ~ IR_FILE_SZ = 1
# ~ #filesz
# ~ IR_FILE_DATE = 2
# ~ #filedate
# ~ IR_DATETIME_ORIG = 3
# ~ #datetimeoriginal
# ~ IR_DATETIME_DIG = 4
# ~ #datetimedigitized
# ~ IR_DATETIME = 5
# ~ #datetime
# ~ IR_MAKE = 6
# ~ #make
# ~ IR_MODEL = 7
# ~ #model
# ~ IR_EXIF_WIDTH = 8
# ~ #exifimagewidth
# ~ IR_EXIF_HEIGHT = 9
# ~ #exifimageheight
# ~ IR_EXIF_VER = 10
# ~ #exifversion
# ~ IR_ORIENTATION = 11
# ~ #orientation
# ~ #epoch Day
# ~ IR_EPOCH_DAY = 12
# ~ #year_day
# ~ IR_YEAR_DAY = 13
# ~ IR_NUM_FIELDS = 14


class ImageRecord:
    def __init__(self, path=None, file_sz=None, file_date=None,aAttr=None, dAttr=None):
        def GetAttrSafe(aAttributes, n, szType):
            try:
                val = aAttributes[n]
            except:
                return (None)
                
            if szType == 'str':
                return (val)
            elif szType == 'int':
                try:
                    return (int(val))
                except:
                    return (None)
            elif szType == 'datetime':
                if isinstance(val,float) or isinstance(val,int):
                    return (datetime.datetime.fromtimestamp(int(val)))
                elif isinstance(val,str):
                    if len(val) == 0:
                        return(None)
                    if len(val) < len('yyyy-mm-dd hh:ss:mm'):
                        try:
                            return( datetime.datetime.fromtimestamp(int(float(val))) )   
                        except:
                            logging.warn(f"Invalid date format value [{val}]")
                            return(None)                            
                    else:
                        szFormat = "%Y-%m-%d %H:%M:%S"
                        if '.' in val:
                            szFormat += ".%f"
                        try:
                            return(datetime.datetime.strptime(val,szFormat))
                        except:
                            logging.warn(f"Invalid date format value [{val}]")
                            return(None)
                else:
                    return(None)
            elif szType == 'bool':
                if isinstance(val,bool):
                    return(val)
                elif isinstance(val,str):
                    if val == 'True':
                        return(True)
                elif isinstance(val,int):
                    if val == 1:
                        return(True)
                return(False)
            else:
                return (val)
        #set all attributes to None
        self.path = None
        self.file_sz = None
        self.dt = None
        self.make = None
        self.model = None
        self.exif_ver = None
        self.width = None
        self.height = None
        self.orientation = None
        self.epoch_day = None
        self.year_day = None
        self.likes = None
        self.favorite = False
        self.last_played = None
        self.edited = None

        if aAttr is not None:
            self.path = GetAttrSafe(aAttr,0,'str')
            self.file_sz = GetAttrSafe(aAttr,1,'int')
            self.dt = GetAttrSafe(aAttr,2,'datetime')
            self.make = GetAttrSafe(aAttr,3,'str')
            self.model = GetAttrSafe(aAttr,4,'str')
            self.exif_ver = GetAttrSafe(aAttr,5,'int')
            self.width = GetAttrSafe(aAttr,6,'int')
            self.height = GetAttrSafe(aAttr,7,'int')
            self.orientation = GetAttrSafe(aAttr,8,'int')
            self.epoch_day = GetAttrSafe(aAttr,9,'int')
            self.year_day = GetAttrSafe(aAttr,10,'int')
            self.likes = GetAttrSafe(aAttr,11,'int')
            self.favorite = GetAttrSafe(aAttr,12,'bool')
            self.last_played = GetAttrSafe(aAttr,13,'datetime')
            self.edited = GetAttrSafe(aAttr,14,'datetime')
        elif dAttr is not None:
            self.path = GetAttrSafe(dAttr,'path','str')
            self.file_sz = GetAttrSafe(dAttr,'file_sz','int')
            self.dt = GetAttrSafe(dAttr,'dt','datetime')
            self.make = GetAttrSafe(dAttr,'make','str')
            self.model = GetAttrSafe(dAttr,'model','str')
            self.exif_ver = GetAttrSafe(dAttr,'exif_ver','int')
            self.width = GetAttrSafe(dAttr,'width','int')
            self.height = GetAttrSafe(dAttr,'height','int')
            self.orientation = GetAttrSafe(dAttr,'orientation','int')
            self.epoch_day = GetAttrSafe(dAttr,'epoch_day','int')
            self.year_day = GetAttrSafe(dAttr,'year_day','int')         
            self.likes = GetAttrSafe(dAttr,'likes','int')
            self.favorite = GetAttrSafe(dAttr,'favorite','bool')
            self.last_played = GetAttrSafe(dAttr,'last_played','datetime')
            self.edited = GetAttrSafe(dAttr,'edited','datetime')
        else:
            self.path = path
            if file_sz is not None and file_date is not None:
                d={}
                d['file_sz'] = file_sz
                d['dt'] = file_date
                self.file_sz = GetAttrSafe(d,'file_sz','int')
                self.dt = GetAttrSafe(d,'dt','datetime')
            else:
                if os.path.exists(path):
                    stats = os.stat(path)
                    d={}
                    d['file_sz'] = stats.st_size
                    d['dt'] = stats.st_mtime
                    self.file_sz = GetAttrSafe(d,'file_sz','int')
                    self.dt = GetAttrSafe(d,'dt','datetime')
                    
        if self.dt is not None:
            if self.epoch_day is None or self.year_day is None:
                self.PopStdDays()
                
        if self.likes is None:
            self.likes = 0
            
    def __repr__(self):
        return(f"{self.path, self.file_sz,self.dt,self.make,self.model,self.exif_ver,self.width,self.height,self.orientation,self.epoch_day,self.year_day,self.likes,self.favorite,self.last_played,self.edited}")
        
    def __iter__(self):
        return iter([ self.path , \
                        self.file_sz , \
                        self.dt, \
                        self.make , \
                        self.model , \
                        self.exif_ver , \
                        self.width , \
                        self.height , \
                        self.orientation , \
                        self.epoch_day , \
                        self.year_day, \
                        self.likes, \
                        self.favorite, \
                        self.last_played, \
                        self.edited \
                         ])
                        
    def PopStdDays(self):
        if self.dt is None:
            return()
        (self.year_day,self.epoch_day) = GetStandardDays(self.dt)
        return()
        

    def PopAttr(self,rootDir=''):
        #Populate Object Attributes from Image File
        photoPath = rootDir + self.path
        #open image file
        #get EXIF information
        #get width, height from image
        #validate
        img = Image.open(photoPath)

        try:
            info = img._getexif()
        except AttributeError:
            logging.warn(f"no EXIF: {photoPath}")
            return
        dTags = {}
        if info is not None:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                dTags[str(decoded).lower()] = value
                
        #populate attributes
        try:
            self.make = dTags['make'].replace("\x00","")
        except:
            pass
        try:
            self.model = dTags['model'].replace("\x00","")
        except:
            pass
        try:            
            self.width = dTags['exifimagewidth']
        except:
            pass
        try:            
            self.height = dTags['exifimageheight']
        except:
            pass
        try:            
            self.exif_ver = dTags['exifversion'].decode('utf-8')
        except:
            pass
        try:            
            self.orientation = dTags['orientation']
        except:
            pass
            
    #add id as set at runtime
    def GetJsonId(self,nId):
        dDict = self.__dict__
        if dDict['dt'] is not None:
            dDict['dt'] = dDict['dt'].timestamp()
        if dDict['last_played'] is not None:
            dDict['last_played'] = dDict['last_played'].timestamp()
        if dDict['edited'] is not None:
            dDict['edited'] = dDict['edited'].timestamp()

        dDict['id'] = nId
        return(json.dumps(dDict,skipkeys=True))
        
    def RotateCW(self):
        #rotate first
        if self.orientation in (None,0,1):
            self.orientation = 3
        elif self.orientation in (3,4):
            self.orientation = 6
        elif self.orientation in (5,6):
            self.orientation = 8
        elif self.orientation in (7,8):
            self.orientation = 0
        self.Edited()
        return()
        
    def ThumbsUp(self):
        self.likes += 1
        #max out on 3 thumbs up
        if self.likes > 3:
            self.likes = 3
        self.Edited()
        return()
        
    def ThumbsDown(self):
        #if favorite, set to false, don't change thumbs down level
        if self.favorite == True:
            self.favorite = False
            self.Edited()
            return()
        #don't allow negative likes as that will set to be blocked
        if self.likes > 0:
            self.likes -= 1
        self.Edited()
        return()
    
    def Favorite(self): 
        self.favorite = True
        #a favorited image can't also be blocked (-1 likes)
        if self.likes < 0:
            self.likes = 0
        self.Edited()
        return()
        
    def UnFavorite(self):
        self.favorite = False
        self.Edited()
        return()
        
    def Block(self):
        self.likes = -1
        #a blocked image (like -1) can't also be a favorite
        self.favorite = False
        self.Edited()
        return()
        
    def Edited(self):
        self.edited = datetime.datetime.now()
        return()
        
#------end ImageRecord definition   

#load in csv file
def LoadIRcsv(fpath):
    aImgRecs = []

    with open(fpath, 'r') as csvfile:
        logging.debug(f"loading records from: {fpath}")
        reader = csv.reader(csvfile)
        for row in reader:
            oIR = ImageRecord(aAttr = row)
            aImgRecs.append(oIR)
    return (aImgRecs)
    
def SaveIRcsv(fpath, aImgRecs, safe=True):
    nFSold = os.path.getsize(fpath)
    if safe and os.path.exists(fpath):
        fold = fpath + ".old"
        logging.info(f"safe save requested moving {fpath} to {fold}")
        os.replace(fpath,fold)
        nFSold = os.path.getsize(fold)
    #write records to csv file
    logging.info(f"saving {len(aImgRecs)} records to {fpath}")
    n = 0
    with open(fpath, 'w') as csvfile:
        csvout = csv.writer(csvfile)
        for row in aImgRecs:
            csvout.writerow(row)
            n += 1
    nFS = os.path.getsize(fpath)

    nFSDeltaPerc = int(abs(float(nFS-nFSold)/float(nFS)))
    logging.debug(f"File size change percentage on save:{nFSDeltaPerc}%")
    if nFSDeltaPerc >= 3:
        logging.warn(f"Large change in file size {nFS} {nFSDeltaPerc}% for file {fpath}")        
    
    #return number records saved and file size
    return(n,nFS)    
        
def GetStandardDays(dt):
    if dt is None:
        return()
    #given datetime return number of days from 1 Jan, 1990 and day of year 
    SECS_IN_DAY = 86400
    dtEPOCH_DAY = datetime.datetime.strptime('1990-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")
    epoch_day = int( (dt-dtEPOCH_DAY).total_seconds()/SECS_IN_DAY )

    #get day of year 
    year_day = dt.timetuple().tm_yday 
    if (dt.year % 100 == 0) & (year_day > 59):
        year_day -= 1
    return(year_day,epoch_day)
    
def DictInc(d,k):
    if k in d:
        d[k]+=1
    else:
        d[k]=1
        
def GetMachineId():
    #remove first 9 characters as that is generated from timestamp and we want non-changing portion
    return(str(uuid.uuid1())[9:])
    
def CheckPathSlash(szP):
    #ensure path ends in slash
    if szP[-1] != '/':
        return(szP + '/')
    else:
        return(szP)
        
def BackupFile(szPath,szBackupPath):    
    # Backup of file
    # check to see if path exists
    if not os.path.exists(szPath):
        logging.warn(f"file {szPath} does not exists")
        return (False)
    # chomp to get directory
    (szHead,szFile) = os.path.split(szPath)
    # make a backup subdirectory
    szBUDir = CheckPathSlash(szBackupPath)
    if not os.path.exists(szBUDir):
        os.mkdir(szBUDir)    
    bSaved = False
    n = 1
    while not bSaved:
        # add .1 to filename
        szBUFilePath = szBUDir + szFile + f".{n}"
        if not os.path.exists(szBUFilePath):
            logging.debug(f"Backedup to {szBUFilePath}")
            shutil.copy(szPath,szBUFilePath)
            bSaved = True
        else:
            # add 1 and try again
            n += 1
    return(szBUFilePath)
    
def SplitToArray(s, c):
    #split string s by character c and chomp spaces
    a = s.split(c)
    for i in range(0,len(a)):
        a[i] = a[i].strip()
    return(a)
