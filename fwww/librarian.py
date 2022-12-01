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
import shutil
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
def RemoveBrokenLinksIRcsv( aImgRecs, szPhotoRoot, mpQueue = None ):
    #check each image record path exists in szPhotoRoot and if not remove from IRcsv
    nBefore = len(aImgRecs)
    szPhotoRoot = CheckPathSlash(szPhotoRoot)
    
    aRemoveIds = []
    for i in range(0,len(aImgRecs)):
        if (i % 2500) == 0:
            Puts(f"Scanning Records {round(i/nBefore*100,1)}% done", mpQueue)
        #check to see if file exists
        if not os.path.exists(szPhotoRoot + aImgRecs[i].path):
            aRemoveIds.insert(0,i)
            logging.debug(f"Id{i} path broken")
    
    #remove r in aImgRecs was not working with a list.  got a not found error so did this hack        
    for i in aRemoveIds:
        logging.debug(f"Id{i} removed")
        aImgRecs.pop(i)
        
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
    
def MoveImageFilesToPhotoRoot( szPhotoRoot, szImportDir, mpQueue = None ):
    szPhotoRoot = CheckPathSlash(szPhotoRoot)
    szImportDir = CheckPathSlash(szImportDir)
    nLenID = len(szImportDir)
    # find new directory
    bFound = False
    n = 0
    while not bFound:
        # add 1 to dirname
        szNewFileDir = szPhotoRoot + f"{n:04d}"
        logging.debug(f"trying {szNewFileDir}")
        if not os.path.exists(szNewFileDir):
            logging.debug(f"Making directory {szNewFileDir}")
            os.mkdir(szNewFileDir)
            bFound = True
        else:
            # add 1 and try again
            n += 1
    szNewFileDir = CheckPathSlash(szNewFileDir)
    logging.debug(f"s:{szImportDir} d:{szNewFileDir}")
    Puts(f"[R]Moving photos to {szNewFileDir}")
    aDirEntries = os.scandir(szImportDir)
    for entry in aDirEntries:
        szDest = szNewFileDir + entry.path[nLenID:]
        logging.debug(f"moving s:{entry.path} d:{szDest}")
        shutil.move(entry.path, szDest)
    return(szNewFileDir)
    

def DatabaseMaintenance( aImgRecs, n, mpQueue = None ):
    ### find all the issues
    ## find and remove broken links (image file deleted on disk but not in database
    Puts(f"[H]Remove Broken Links",mpQueue)
    Puts(f"Removing broken links. Starting...",mpQueue)
    nLenBefore = len(aImgRecs)
    RemoveBrokenLinksIRcsv(aImgRecs,cfg.get('PATHS','photo_root_path'),mpQueue)
    Puts(f"[R]Found {nLenBefore-len(aImgRecs)} broken links. {len(aImgRecs)} records remaining",mpQueue)

    Puts(f"[H]Seek Orphaned Photos",mpQueue)
    Puts(f"Seeking orphaned photos. Starting...",mpQueue)    
    aNewImages = VerifyIRcsvToPhotoDir(aImgRecs,cfg.get('PATHS','photo_root_path'),mpQueue)
    Puts(f"[R]Found {len(aNewImages)} images not in database.",mpQueue)
    
    ## find orphan images (image file on disk but not in database)
    ## update orphans with image data (slow)
    Puts(f"[H]Getting image data",mpQueue)
    Puts(f"Getting image data. Starting...",mpQueue)    
    aNewIRs = GetNewImgRecsFromPaths(aNewImages,cfg.get('PATHS','photo_root_path'))
    aImgRecs += aNewIRs
    Puts(f"[R]Added {len(aNewIRs)} images to database",mpQueue)
    
    # if issues found, back up the image rec file and save new
    
def ImportPhotos( aImgRecs, n, mpQueue = None ):
    ### get list of photo paths to import
    ### make new subdirectory in photo root
    ### move each file to new location, adding to list of new photos
    ### make new image records
    ### add new image records to database
    Puts(f"[H]Looking for New Photos",mpQueue)
    Puts(f"Looking for new photos. Starting...",mpQueue)
    nLenBefore = len(aImgRecs)
    aImportImgs = GetImagePathsFromDirectory(cfg.get('PATHS','import_photo_path'))
    nImport = len(aImportImgs)
    if nImport == 0:
        Puts(f"[R]Found no images for importing in {cfg.get('PATHS','import_photo_path')}",mpQueue)
        return
    Puts(f"[R]Found {len(aImportImgs)} images for importing",mpQueue)
 
    Puts(f"[H]Moving Photo files",mpQueue)
    Puts(f"Moving photo files. Starting...",mpQueue)    
    szNewImageDir = MoveImageFilesToPhotoRoot(cfg.get('PATHS','photo_root_path'),cfg.get('PATHS','import_photo_path'), mpQueue)
    Puts(f"[H]Getting Image Data", mpQueue)
    Puts(f"[H]Getting Image Data. Starting...", mpQueue)
    aImportImgPaths = GetImagePathsFromDirectory(szNewImageDir)
    if (nImport != len(aImportImgPaths)):
        logging.error(f"Possible move error to {szNewImageDir}. Expected {nImport} found {len(aImportImgPaths)} records")
    aNewIRs = GetNewImgRecsFromPaths(aImportImgPaths,cfg.get('PATHS','photo_root_path'))
    aImgRecs += aNewIRs
    Puts(f"[R]Added {len(aNewIRs)} images to database",mpQueue)
    
#----------MAIN------------    
if __name__ == '__main__':
    #setup
    logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')
    logging.getLogger().setLevel(logging.DEBUG)
        
    tStart = time.process_time()

    # ~ multiprocessing.set_start_method('spawn')
    # ~ q = multiprocessing.Queue()
    # ~ p = multiprocessing.Process(target=testloop, args=(q,))

    # ~ testloop(q)

    # ~ szBUPath = CheckPathSlash(cfg.get('PATHS','miframe_etc_path')) + 'backup/'    
    # ~ BackupFile(cfg.get('PATHS','image_records_file'),szBUPath)
    
    aImageRecords = LoadIRcsv(cfg.get('PATHS','image_records_file'))
    tLoad = time.process_time()
    logging.info(f"Load Time:\t{tLoad-tStart}")
    
    # ~ DatabaseMaintenance(aImageRecords)
    # ~ tGroom = time.process_time()
    # ~ logging.info(f"Groom Time:\t{tGroom-tLoad}")
    
    ImportPhotos(aImageRecords, 0)
    tGroom = time.process_time()
    logging.info(f"Import Time:\t{tGroom-tLoad}")    
    
    # ~ aImageRecords = RemoveBrokenLinksIRcsv(aImageRecords,cfg.get('PATHS','photo_root_path'))
    # ~ tGroom = time.process_time()
    # ~ logging.debug(f"Groom Time:\t{tGroom-tLoad}")
    
    # ~ aNewImages = ['/media/sf_Our_Pictures/test/dscf0010.jpg', '/media/sf_Our_Pictures/test/GatheringStorm.jpg', '/media/sf_Our_Pictures/test/IMG_0026.jpg', '/media/sf_Our_Pictures/test/IMG_1681.JPG', '/media/sf_Our_Pictures/test/IMG_4550.JPG', '/media/sf_Our_Pictures/test/LandOfTheFreeManzanarBasketball.jpg', '/media/sf_Our_Pictures/test/Polaris.jpg', '/media/sf_Our_Pictures/test/PyramidsAndPolygons.jpg', '/media/sf_Our_Pictures/test/Serenity.jpg', '/media/sf_Our_Pictures/test/StargazingAtHarmonyBoraxWorks.jpg', '/media/sf_Our_Pictures/test/SteppingStones.jpg']

    # ~ aNewImages = VerifyIRcsvToPhotoDir(aImageRecords,cfg.get('PATHS','photo_root_path'))
    # ~ tVerify = time.process_time()
    # ~ logging.debug(f"New Images Found:\t{len(aNewImages)}")
    # ~ logging.debug(f"Verify Time:\t{tVerify-tGroom}")
    
    # ~ aNewIRs = GetNewImgRecsFromPaths(aNewImages,cfg.get('PATHS','photo_root_path'))
    # ~ aImageRecords += aNewIRs
    # ~ tNewRecs = time.process_time()
    # ~ logging.debug(f"New Records Time:\t{tNewRecs - tVerify}")
    
    # ~ for r in aNewIRs:
        # ~ print(r)
    
    #save changes
    nRec = 0; nFSize = 0
    # ~ (nRec, nFSize) = SaveIRcsv(cfg.get('PATHS','image_records_file'), aImageRecords, safe=False)
    tSave = time.process_time()    
    logging.info(f"Records Saved {nRec} File Size {nFSize} bytes")
    # ~ logging.debug(f"Save Time:\t{tSave - tNewRecs}")
    
    tEnd = time.process_time()
    logging.info(f"Elapsed Time:\t{tEnd-tStart}")
