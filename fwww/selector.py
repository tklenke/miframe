import src.config as mifcfg
import csv
import datetime, time
import logging
import random
import json
#sudo apt-get install python3-scipy
import scipy.stats as stats

#setup
logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')

#miframe specific includes
from src.mif import ImageRecord
from src.mif import DictInc

#load in csv file
## build list of photos/epoch day
## get list of outlier epoch days
#select a file
## filter orientation
## filter blocked, disliked
## filter date, day
## filter liked
## most likely should be log decay of day of year, tomorrow most likely, yesterday not at all likely
#serve the file

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
    

def GetWeirdEpochDays(aImgRecs):
#get array of epoch days out of normal distribution
    aWeirdEpochDays = []
    #build dict of Epoch Days and count of each
    dED = {}
    for rec in aImgRecs:
        DictInc(dED,rec.epoch_day)

    #calc stats on all nonzero days
    fMean = stats.tmean(list(dED.values()))
    fStd = stats.tstd(list(dED.values()))

    nOutlierThreshold = int(fMean + mifcfg.threshold_num_std_dev * fStd)
    logging.debug(f"Mean:{fMean} Std Dev:{fStd}  Threshold:{nOutlierThreshold}")
    
    for key in dED.keys():
        if dED[key] > nOutlierThreshold:
            aWeirdEpochDays.append(key)        
    
    return(aWeirdEpochDays)

def GetIdsYrDay(aImgRecs):
#get dict of arrays of day of year, excluding weird epoch days
    dYearDayIds = {}
    
    #get list of weird epoch days
    aWeirdEDs = GetWeirdEpochDays(aImgRecs)
    logging.debug(f"Found {len(aWeirdEDs)} weird epoch days")
    
    for i in range(0,len(aImgRecs)-1):
        if aImgRecs[i].year_day not in dYearDayIds:
            dYearDayIds[aImgRecs[i].year_day] = []
        dYearDayIds[aImgRecs[i].year_day].append(i)
    
    return (dYearDayIds)
    


#GetNext Image ID
## calling program should do the following
### Get array of ids from Shuffle
### pop from array until Shuffle Array is empty
### Get new array of ids from Shuffle   

def Shuffle(aImgRecs):
    def GetIdsNDays( dIds, nDoY, n):
        a = []
        for i in range(nDoY,nDoY+n):
            nDay = ((i + 365) % 365) + 1  
            # ~ logging.debug(f"i[{i}] DOY:{nDay}")
            a += dIds[nDay]
        return(a)
        
#build list of picts to show
##num fully random
##num upcoming year days
##num liked
##num favorties
    nRandom = mifcfg.random_weight
    nUnseen = mifcfg.unseen_weight
    nUpcoming = mifcfg.upcoming_weight
    nLiked = mifcfg.liked_weight
    nFavorites = mifcfg.favorites_weight
    
    aShuffleIds = []
    
    #pick random of everything that has not been blocked/unliked
    i = 0
    while i < nRandom:
        rId = random.randrange(0,len(aImgRecs),1)
        if aImgRecs[rId].likes > -1:
            i += 1
            aShuffleIds.append(rId)
            
    #pick random of everything that has not been seen
    i = 0        
    while i < nUnseen:
        rId = random.randrange(0,len(aImgRecs),1)
        if aImgRecs[rId].last_played is None:
            i += 1
            aShuffleIds.append(rId)
            
    #pick random of photos taken in day of year in near future
    i = 0
    ## get array of year days with list of record ids for each
    dIdsByYearDay = GetIdsYrDay(aImgRecs)
    logging.debug(f"Found {len(dIdsByYearDay.keys())} days of year")
    ## build array of ids from upcoming days
    ### get current day of the year
    ### get all ids from next 3, 15, 30, 90 days and put into array
    nTodayYearDay = datetime.datetime.now().timetuple().tm_yday
    #### get ids from next 3,15,30,90 days
    aUpcomingIds = GetIdsNDays(dIdsByYearDay,nTodayYearDay,3)
    aUpcomingIds += GetIdsNDays(dIdsByYearDay,nTodayYearDay,15)
    aUpcomingIds += GetIdsNDays(dIdsByYearDay,nTodayYearDay,30)
    aUpcomingIds += GetIdsNDays(dIdsByYearDay,nTodayYearDay,90)
    while i < nUpcoming:
        rId = random.choice(aUpcomingIds)
        if rId not in aShuffleIds:
            i += 1
            aShuffleIds.append(rId)
    # ~ i = 0        
    # ~ while i < nLiked:
    # ~ #pick random of everything that has been liked
        # ~ rId = random.randrange(0,len(aImgRecs),1)
        # ~ if aImgRecs[rId].likes > 0:
            # ~ i += 1
            # ~ aShuffleIds.append(rId)            
    # ~ i = 0        
    # ~ while i < nFavorites:
    # ~ #pick random of everything that has been liked
        # ~ rId = random.randrange(0,len(aImgRecs),1)
        # ~ if aImgRecs[rId].favorite:
            # ~ i += 1
            # ~ aShuffleIds.append(rId)            
    
    #shuffle the array well    
    for i in range(0,10):
        random.shuffle(aShuffleIds)
        
    return(aShuffleIds)    
    
            


#----------MAIN------------    
if __name__ == '__main__':
    tStart = time.process_time()
    
    logging.getLogger().setLevel(logging.DEBUG)
    
    aImageRecords = LoadIRcsv(mifcfg.image_records_file_read)
    logging.debug(f"Read {len(aImageRecords)} image records")
    
    aWeirdDays = GetWeirdEpochDays(aImageRecords)
    logging.debug(f"Found {len(aWeirdDays)} weird days")
    
    logging.debug(f"Shuffling image records")
    aIds = Shuffle(aImageRecords)
    logging.debug(f"Done shuffling")
    

    for i in range(0,1):
        irand = aIds.pop()
        szJSON = aImageRecords[irand].GetJsonId(irand)
        dJAttr = json.loads(szJSON)
        print (dJAttr)
        ir = ImageRecord(dAttr = dJAttr)
        print(ir)
    
    tEnd = time.process_time()
    logging.debug(f"Elapsed Time:\t{tEnd-tStart}")
