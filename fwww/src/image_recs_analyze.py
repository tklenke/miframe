import config as mifcfg
import os
import datetime, time
import csv
#sudo apt-get install python3-scipy
import scipy.stats as stats
import logging
import logging
logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')
#logging.getLogger().setLevel(logging.DEBUG)


#MiFrame Shared library
from mif import ImageRecord
from mif import GetStandardDays
from mif import DictInc


aWeirdDays = [5840,5841,5842,11130,11131]

#-------------Funtions
    


#--------------MAIN
if __name__ == '__main__':
    tStart = time.process_time()
    aImgRecs = []

    with open(mifcfg.image_records_file_read, 'r') as csvfile:
        logging.info(f"Reading file:\t{mifcfg.image_records_file_read}")        
        reader = csv.reader(csvfile)
        for row in reader:
            oIR = ImageRecord(aAttr = row)
            aImgRecs.append(oIR)


    (nDayOfYear,nEpochDays) = GetStandardDays(datetime.datetime.now())
    dtEPOCH_DAY = datetime.datetime.fromtimestamp(mifcfg.ts_epoch_day)
    tsEPOCH_DAY = datetime.datetime.timestamp(dtEPOCH_DAY)
    logging.info(f"Today is {nEpochDays} days from timestamp {tsEPOCH_DAY} {str(dtEPOCH_DAY)}") 
    
    dCamera = {}
    dExifVer = {}
    dOrientation = {}
    nMinFSz = 1000000
    nMaxFSz = 0
    nNoFileDate = 0
    nNoDTOrig = 0
    nNoDTDig = 0
    nNoDT = 0
    nDTFTgt1Day = 0
    aPicsOnYearDay = []
    aPicsOnEpochDay = []
    for i in range(0,366):
        aPicsOnYearDay.append(0)
    for i in range(0, nEpochDays):
        aPicsOnEpochDay.append(0)


    for rec in aImgRecs:
        DictInc(dCamera,str(rec.make) + '|' + str(rec.model))
        DictInc(dExifVer,str(rec.exif_ver))
        DictInc(dOrientation,str(rec.orientation))
        if rec.file_sz < nMinFSz:
            nMinFSz = rec.file_sz
        if rec.file_sz > nMaxFSz:
            nMaxFSz = rec.file_sz
        #check dates
        # ~ if rec[ys.IR_FILE_DATE] == None:
            # ~ nNoFileDate +=1
        # ~ if rec[ys.IR_DATETIME_ORIG] == None:
            # ~ nNoDTOrig +=1
        # ~ if rec[ys.IR_DATETIME_DIG] == None:
            # ~ nNoDTDig +=1
        # ~ if rec[ys.IR_DATETIME] == None:
            # ~ nNoDT +=1
        # ~ try:
            # ~ nDateDiffSec = abs((rec[ys.IR_FILE_DATE]-rec[ys.IR_DATETIME]).total_seconds())
        # ~ except TypeError:
            # ~ nDateDiffSec = SECS_IN_DAY*10
        # ~ if nDateDiffSec > SECS_IN_DAY:
            # ~ nDTFTgt1Day +=1
        aPicsOnYearDay[rec.year_day] += 1
        aPicsOnEpochDay[rec.epoch_day] += 1
        
    nTotalPicsOnNonZeroDays = 0
    dDaysNPics = {}
    bFirstDayFound = False
    aNonZeroDays = []
    for i in range(0,nEpochDays):
        if aPicsOnEpochDay[i] > 0:
            aNonZeroDays.append(aPicsOnEpochDay[i])
            nTotalPicsOnNonZeroDays += aPicsOnEpochDay[i]
            DictInc(dDaysNPics,aPicsOnEpochDay[i])
            
    logging.info(str("Non Zero Days:{} Total Pics:{}  Avg Pics/Day:{}".format(len(aNonZeroDays),\
        nTotalPicsOnNonZeroDays, nTotalPicsOnNonZeroDays/len(aNonZeroDays))))
    
    #calc stats on all nonzero days
    fMean = stats.tmean(aNonZeroDays)
    fStd = stats.tstd(aNonZeroDays)
    
    nOutlierThreshold = int(fMean + mifcfg.threshold_num_std_dev * fStd)
    logging.info(f"Mean:{fMean} Std Dev:{fStd}  Threshold:{nOutlierThreshold}")
    
    #build list of outlier epoch days
    aOutlierEpochDays = []
    for i in range(1, nEpochDays):
        if aPicsOnEpochDay[i] > nOutlierThreshold:
            aOutlierEpochDays.append(i)
            
    #recalc pics on year days without outliers
    nOutlierDaysTrimmed = 0
    for rec in aImgRecs:
        if rec.epoch_day in aOutlierEpochDays:
            # ~ logging.debug(f"Outlier epoch day:\t{i}")
            nOutlierDaysTrimmed +=1
        else:
            aPicsOnYearDay[rec.year_day] += 1
            
    aPicDay = []
    for i in range(1,366):
        a = []
        a.append(float(i))
        a.append(float(aPicsOnYearDay[i]))
        aPicDay.append(a)

    # ~ (a,b) = cluster.kmeans2(aPicDay,15)
    # ~ print("kmeans cluster: {}".format(a))
    
    # ~ #clusters = hcluster.fclusterdata(aPicDay, 15.0, criterion="distance")
    # ~ clusters = hcluster.fclusterdata(aPicDay, 10ip.0)
    # ~ print("hcluser: {}".format(clusters))



    for key in sorted(dDaysNPics.keys()):
        logging.debug(f"Pics on Day {key} Num Days{dDaysNPics[key]}")

    
    logging.info(f"Cameras")
    for key in dCamera.keys():
        logging.info(f"{key}\t{str(dCamera[key])}")
    logging.info(f"EXIF Versions")
    for key in dExifVer.keys():
        logging.info(f"{key}\t{str(dExifVer[key])}")
    logging.info(f"Orientation")
    for key in dOrientation.keys():
        logging.info(f"{key}\t{str(dOrientation[key])}")  

    logging.info(f"Histogram of Pics by Day of the Year") 
    doy = dtEPOCH_DAY
    total_imgs = 0
    for i in range(1,366):
        logging.info(f"[{i}] {str(doy)}:\t{str(aPicsOnYearDay[i])}")  
        doy = doy + datetime.timedelta(days = 1)
        total_imgs += aPicsOnYearDay[i]
    logging.info(f"Total Imgs by Day of Year:\t{total_imgs}") 
            
    logging.info(f"File Size Max:\t{nMaxFSz}\tMin:\t{nMinFSz}")  
    logging.info(f"Missing Date:File\t{nNoFileDate}\tOrig:{nNoDTOrig}\tDigtz:\t{nNoDTDig}\tDT:\t{nNoDT}") 
    logging.info(f"Datetime File Time unmatched:\t{nDTFTgt1Day}") 
           
    logging.info(f"Input Records:\t{len(aImgRecs)}")        
    logging.info(f"Elapsed Time:\t{time.process_time()-tStart}")        

