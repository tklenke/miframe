####
##  Librarian module is resposible for following tasks
##   # initial building of image record csv from images in photo library
##   # importing of new images from new image directory in photo library and updating image record csv
##   # clean-up of image record csv by removing links to images that have been deleted from photo library
##   # sequestering of blocked images and clean up of image record csv
##   # text depiction of photo library (text tree view)
##
##  BuildIRcsv(directory)
##
##
##
##
###
import configparser
import time
import logging
import os
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS
from src.mif import ImageRecord, BackupFile, SplitToArray, LoadIRcsv, SaveIRcsv, CheckPathSlash
from mpwrapper import Puts

###---Start up Tasks---
logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')
cfg = configparser.ConfigParser()
g_szIniPath = os.getenv('MIFRAME_INI', '/home/admin/projects/miframe/fwww/miframe.ini')
if not os.path.exists(g_szIniPath):
    logging.critical(f"Can't find config file {g_szIniPath}")
    exit()
cfg.read(g_szIniPath)

###-----Funtions--------------
#so we can break from a deep loop
class ContinueI(Exception):
    pass
    
continue_i = ContinueI()


def GetDirsOS(directory,aSkipDirs):
    # ~ logging.debug(f"Dir: {directory}")
    aScans = os.scandir(directory)
    dirs = []
    for scan in aScans:
        try:
            #skip 
            for skipdir in aSkipDirs:
                if scan.name == skipdir:
                    logging.debug(f"Skipping: {scan.name}")
                    raise continue_i
        except ContinueI:
            continue
            
        if scan.is_dir():
            directory = CheckPathSlash(directory)
            newdir = directory + scan.name
            dirs.append(newdir)
            #go recursive
            dirs = dirs + GetDirsOS(newdir,aSkipDirs)
    return(dirs)   
    
def GetImagePathsFromDirectory(directory):
    # ~ logging.debug(f"Dir: {directory}")
    aImgPaths = []

    aDirEntries = os.scandir(directory)
    for entry in aDirEntries:
        if entry.is_file():
            (root,ext)=os.path.splitext(entry.name)
            ext = ext.lower()
            if '.jpg' == ext:
                stats = entry.stat()
                aImgPaths.append(entry.path)
    return(aImgPaths)


#-------Exported Functions--------------
def RemoveBrokenLinksIRcsv( aImgRecs, szPhotoRoot ):
    #check each image record path exists in szPhotoRoot and if not remove from IRcsv
    nBefore = len(aImgRecs)
    szPhotoRoot = CheckPathSlash(szPhotoRoot)
    
    for r in aImgRecs:
        #check to see if file exists
        if not os.path.exists(szPhotoRoot + r.path):
            logging.debug(f"Removing {r.path} from image records")
            aImgRecs.remove(r)
        
    logging.debug(f"Image Records: Before {nBefore} After {len(aImgRecs)} grooming")
    return(aImgRecs)
    
def VerifyIRcsvToPhotoDir( aImgRecs, szPhotoRoot, mpQueue=None ):
    aNewImgPaths = []
    aIRPaths = []
    nPhotoRootChars = len(szPhotoRoot)
    #build array of existing image paths
    for r in aImgRecs:
        aIRPaths.append(r.path)
    ###get list of directories
    szPhotoRoot = CheckPathSlash(szPhotoRoot)
    #build list of skip directories
    aSkipDirectories = SplitToArray(cfg.get('PATHS','skip_directories'),',')
    #skip miframe_etc and import dirs if in the photo_root
    if szPhotoRoot == (cfg.get('PATHS','miframe_etc_path')[:len(szPhotoRoot)]):
        aSkipDirectories.append(CheckPathSlash(cfg.get('PATHS','miframe_etc_path'))[len(szPhotoRoot):-1])
    if szPhotoRoot == (cfg.get('PATHS','import_photo_path')[:len(szPhotoRoot)]):
        aSkipDirectories.append(CheckPathSlash(cfg.get('PATHS','import_photo_path'))[len(szPhotoRoot):-1])
    #get list of directories
    Puts(f"Scanning Directories...", mpQueue)
    aDirs = GetDirsOS(szPhotoRoot,aSkipDirectories)
    
    #for each directory see if jpg exists in aImgRecs
    n = 0
    for directory in aDirs:
        if n % 20 == 0:
            Puts(f"Scanning Directories {round(n/len(aDirs)*100,1)}% done", mpQueue)
        n += 1
        aImgPaths = GetImagePathsFromDirectory(directory)
        for path in aImgPaths:
            if not path[nPhotoRootChars:] in aIRPaths:
                logging.debug(f"new image {path}")
                aNewImgPaths.append(path)       
    return(aNewImgPaths)

def GetNewImgRecsFromPaths( aNewImgPaths, szPhotoRoot, mpQueue = None ):
    nPRLen = len(CheckPathSlash(szPhotoRoot))
    Puts(f"Scanning Images", mpQueue)
    aImgRecs = []
    n = 0
    for szPath in aNewImgPaths:
        if n % 20 == 0:
            Puts(f"Scanning Images {round(n/len(aNewImgPaths)*100,1)}% done", mpQueue)
        n += 1
        r = ImageRecord(path=szPath)
        r.PopAttr()
        #trim photo root from path
        r.path = r.path[nPRLen:]
        aImgRecs.append(r)
    return(aImgRecs)

def testloop(q):
    Puts("starting",q)
    i = 1
    while i:
        puts(str(i),q)
        time.sleep(.1)
        i += 1
        if i > 4:
            i = False
    puts("done",q)
    return()
    
#----------MAIN------------    
if __name__ == '__main__':
    #setup
    logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')
    logging.getLogger().setLevel(logging.INFO)
        
    tStart = time.process_time()

    # ~ multiprocessing.set_start_method('spawn')
    # ~ q = multiprocessing.Queue()
    # ~ p = multiprocessing.Process(target=testloop, args=(q,))

    # ~ testloop(q)

    szBUPath = CheckPathSlash(cfg.get('PATHS','miframe_etc_path')) + 'backup/'    
    BackupFile(cfg.get('PATHS','image_records_file'),szBUPath)
    
    aImageRecords = LoadIRcsv(cfg.get('PATHS','image_records_file'))
    tLoad = time.process_time()
    logging.debug(f"Load Time:\t{tLoad-tStart}")
    
    aImageRecords = RemoveBrokenLinksIRcsv(aImageRecords,cfg.get('PATHS','photo_root_path'))
    tGroom = time.process_time()
    logging.debug(f"Groom Time:\t{tGroom-tLoad}")
    
    aNewImages = ['/media/sf_Our_Pictures/test/dscf0010.jpg', '/media/sf_Our_Pictures/test/GatheringStorm.jpg', '/media/sf_Our_Pictures/test/IMG_0026.jpg', '/media/sf_Our_Pictures/test/IMG_1681.JPG', '/media/sf_Our_Pictures/test/IMG_4550.JPG', '/media/sf_Our_Pictures/test/LandOfTheFreeManzanarBasketball.jpg', '/media/sf_Our_Pictures/test/Polaris.jpg', '/media/sf_Our_Pictures/test/PyramidsAndPolygons.jpg', '/media/sf_Our_Pictures/test/Serenity.jpg', '/media/sf_Our_Pictures/test/StargazingAtHarmonyBoraxWorks.jpg', '/media/sf_Our_Pictures/test/SteppingStones.jpg']

    aNewImages = VerifyIRcsvToPhotoDir(aImageRecords,cfg.get('PATHS','photo_root_path'))
    tVerify = time.process_time()
    logging.debug(f"New Images Found:\t{len(aNewImages)}")
    logging.debug(f"Verify Time:\t{tVerify-tGroom}")
    
    aNewIRs = GetNewImgRecsFromPaths(aNewImages,cfg.get('PATHS','photo_root_path'))
    aImageRecords += aNewIRs
    tNewRecs = time.process_time()
    logging.debug(f"New Records Time:\t{tNewRecs - tVerify}")
    
    # ~ for r in aNewIRs:
        # ~ print(r)
    
    #save changes
    nRec = 0; nFSize = 0
    # ~ (nRec, nFSize) = SaveIRcsv(cfg.get('PATHS','image_records_file'), aImageRecords, safe=False)
    tSave = time.process_time()    
    logging.debug(f"Records Saved {nRec} File Size {nFSize} bytes")
    logging.debug(f"Save Time:\t{tSave - tNewRecs}")
    
    tEnd = time.process_time()
    logging.info(f"Elapsed Time:\t{tEnd-tStart}")
