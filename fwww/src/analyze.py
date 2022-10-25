import config as mifcfg
import os
# ~ import io
import datetime, time
import csv
import logging
logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')
#logging.getLogger().setLevel(logging.DEBUG)


#for photos
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS

#miframe specific includes
from mif import ImageRecord

PILLOW_BLOCK_SIZE = mifcfg.pillow_image_buffer_size
PILLOW_BLOCKS_MAX  = 30

#so we can break from a deep loop
class ContinueI(Exception):
    pass
    
continue_i = ContinueI()

def GetDirsOS(directory):
    logging.debug(f"Dir: {directory}")
    aScans = os.scandir(directory)
    dirs = []
    skipdirs = mifcfg.skip_directories
    skipdirs.append(mifcfg.dupes_directory)
    for scan in aScans:
        try:
            #skip 
            for skipdir in skipdirs:
                if scan.name == skipdir:
                    logging.debug(f"Skipping: {scan.name}")
                    raise continue_i
        except ContinueI:
            continue
            
        if scan.is_dir():
            if directory[-1] != '/':
                newdir = directory + '/' + scan.name
            else:
                newdir = directory + scan.name
            dirs.append(newdir)
            if mifcfg.recursive_dirs:
                dirs = dirs + GetDirsOS(newdir)
    return dirs   
    
def GetImageRecordsFromDirectory(directory):
    logging.debug(f"Dir: {directory}")
    aImgRecs = []

    aDirEntries = os.scandir(directory)
    for entry in aDirEntries:
        if entry.is_file():
            (root,ext)=os.path.splitext(entry.name)
            ext = ext.lower()
            if '.jpg' == ext:
                stats = entry.stat()
                #strip off photo_directory from path
                path = entry.path[g_nPhotoDirLen:]
                aImgRecs.append(ImageRecord(path, stats.st_size, stats.st_mtime))
    return(aImgRecs)



#----------MAIN------------    
if __name__ == '__main__':

#build list of img recs using file system info (path, file sz, file date, extension)
#open each file and populate img rec with EXIF and image data
#write img recs to csv file
#read back
    tStart = time.process_time()
    

    #make sure photo_directory ends in '/'
    if mifcfg.photo_root_path[-1] != '/':
        g_szRootDir = mifcfg.photo_root_path + '/'
    else:
        g_szRootDir = mifcfg.photo_root_path
    g_nPhotoDirLen = len(g_szRootDir)
    #get list of directories via recursion
    logging.info(f"Scanning photo root directory: {g_szRootDir}")
    dirs = GetDirsOS(g_szRootDir)

    
    #build array of image recs by scanning each directory for jpgs
    logging.info(f"Scanning {len(dirs)} directories for photos")
    aImageRecords = []
    for directory in dirs:
        aImageRecords = aImageRecords + GetImageRecordsFromDirectory(directory)
    logging.info(f"Found {len(aImageRecords)} photos")
    
    #prune for debugging
    # ~ modulus = int(len(aImageRecords)/2000)
    # ~ for i in range(0,len(aImageRecords)):
        # ~ if i%modulus != 0:
            # ~ aImageRecords.pop()
    # ~ print(f"pruned number records: {len(aImageRecords)}")
    
    #open each image file and populate image rec with EXIF and image data
    i = 0
    for imgRec in aImageRecords:
        imgRec.PopAttr(g_szRootDir)
        i += 1
        if i % 1000 == 0:
            logging.info(f"Scanning imgs, {i} completed")


    #write records to csv file
    logging.info(f"saving records to {mifcfg.image_records_file_write}")
    with open(mifcfg.image_records_file_write, 'w') as csvfile:
        csvout = csv.writer(csvfile)
        for row in aImageRecords:
            csvout.writerow(row)
            
    print(aImageRecords[1:10])
    
    
    tEnd = time.process_time()
    logging.info(f"Elapsed Time:\t{tEnd-tStart}")
