import src.config as mifcfg
import csv
import datetime, time
import logging
import random
import json
#sudo apt-get install python3-scipy
import scipy.stats as stats

#miframe specific includes
from src.mif import ImageRecord, DictInc, LoadIRcsv, SaveIRcsv, GetMachineId

#setup
logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')


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
    logging.debug(f"Mean:{fMean:.2f} Std Dev:{fStd:.2f}  Threshold:{nOutlierThreshold}")
    
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
        if aImgRecs[i].epoch_day not in aWeirdEDs:
        # check to see that it's not one of the weird epoch days as that will swamp the other days
            if aImgRecs[i].year_day not in dYearDayIds.keys():
            #make sure that we have an array at that Year Day in the dict
                dYearDayIds[aImgRecs[i].year_day] = []
            dYearDayIds[aImgRecs[i].year_day].append(i)
    
    return (dYearDayIds)
    
def GetBlockedIds(aImgRecs):
    aBIds = []
    for i in range(0, len(aImgRecs)):
        if aImgRecs[i].likes < 0:
            aBIds.append(i)
    return(aBIds)
    
def GetFavoriteIds(aImgRecs):
    aFIds = []
    for i in range(0, len(aImgRecs)):
        if aImgRecs[i].favorite:
            aFIds.append(i)
    return(aFIds)
    
def GetLikedIds(aImgRecs, nLikes):
    aLIds = []
    for i in range(0, len(aImgRecs)):
        if aImgRecs[i].likes == nLikes:
            aLIds.append(i)
    return(aLIds)

def GetEditedSinceIds(aImgRecs,dt):
    aEIds = []
    for i in range(0, len(aImgRecs)):
        if aImgRecs[i].edited is not None and aImgRecs[i].edited > dt:
            aEIds.append(i)
    return(aEIds)    


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
        #skip blocked
        if aImgRecs[rId].likes < 0:
            continue;
        i += 1
        aShuffleIds.append(rId)
            
    #pick random of everything that has not been seen
    i = 0        
    while i < nUnseen:
        rId = random.randrange(0,len(aImgRecs),1)
        #skip blocked
        if aImgRecs[rId].likes < 0:
            continue;
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
    logging.debug(f"Shuffling {len(aUpcomingIds)} Upcoming Recs")
    while i < nUpcoming:
        rId = random.choice(aUpcomingIds)
        #skip blocked
        if aImgRecs[rId].likes < 0:
            continue;
        if rId not in aShuffleIds:
            i += 1
            aShuffleIds.append(rId)
    
    #Get random of ThumbsUp photos once we have enough liked photos
    i = 0        
    aLikedIds = GetLikedIds(aImgRecs,3)
    aLikedIds += GetLikedIds(aImgRecs,2)
    aLikedIds += GetLikedIds(aImgRecs,1)
    logging.debug(f"Shuffling {len(aLikedIds)} Liked Recs")
    if len(aLikedIds) > nLiked:
        while i < nLiked:
            #pick random of everything that has been liked
            rId = random.choice(aLikedIds)
            #skip blocked not needed
            if rId not in aShuffleIds:
                i += 1
                aShuffleIds.append(rId)
                
    #Get random of Favorited photos once we have enough liked photos
    i = 0
    aFavoriteIds = GetFavoriteIds(aImgRecs)
    logging.debug(f"Shuffling {len(aFavoriteIds)} Favorite Recs")
    if len(aFavoriteIds) > nFavorites:
        while i < nFavorites:
            #pick random of everything that has been liked
            rId = random.choice(aFavoriteIds)
            #skip blocked not needed
            if rId not in aShuffleIds:
                i += 1
                aShuffleIds.append(rId)
    else:
        aShuffleIds += aFavoriteIds
                
    #shuffle the array well    
    for i in range(0,10):
        random.shuffle(aShuffleIds)
        
    return(aShuffleIds)    
    
            


#----------MAIN------------    
if __name__ == '__main__':
    tStart = time.process_time()
    
    logging.getLogger().setLevel(logging.DEBUG)
    
    aImageRecords = LoadIRcsv(mifcfg.image_records_file_read)
    tLoad = time.process_time()
    logging.debug(f"Read {len(aImageRecords)} image records [{tLoad-tStart}]")
    
    aWeirdDays = GetWeirdEpochDays(aImageRecords)
    tWeird = time.process_time()
    logging.debug(f"Found {len(aWeirdDays)} weird days [{tWeird-tLoad}]")
    
    for n in range(1,4):
        logging.debug(f"Found {len(GetLikedIds(aImageRecords,n))} ids liked level [{n}]")
    logging.debug(f"Found {len(GetFavoriteIds(aImageRecords))} favorites")
    logging.debug(f"Found {len(GetBlockedIds(aImageRecords))} blocked")
    tLFB = time.process_time()
    logging.debug(f"Liked, Fav, Blocked time [{tLFB-tWeird}]")
    
    logging.debug(f"Shuffling image records")
    aIds = Shuffle(aImageRecords)
    tShuffle = time.process_time()
    logging.debug(f"Done shuffling [{tShuffle-tLFB}]")
    
    #make some test cases
    a1 = [1000,1001,1002,3000,3001]
    a2 = [1100,1101,1102,3100,3101]
    a3 = [11100,11101,11102,13100,13101]
    a4 = [21100,21101,21102,23100,23101]
    a5 = [2200,2201,2202,2300,2301]
    
    #set status for a few sets of test records
    # ~ for i in a1:
        # ~ aImageRecords[i].ThumbsUp()
    # ~ for i in a2:
        # ~ aImageRecords[i].ThumbsUp()
        # ~ aImageRecords[i].ThumbsUp()
    # ~ for i in a3:
        # ~ aImageRecords[i].ThumbsUp()
        # ~ aImageRecords[i].ThumbsUp()
        # ~ aImageRecords[i].ThumbsUp()
        # ~ aImageRecords[i].ThumbsUp()
    # ~ for i in a4:
        # ~ aImageRecords[i].Favorite()
    # ~ for i in a5:
        # ~ aImageRecords[i].Block()        

    # ~ for i in range(0,1):
        # ~ irand = aIds.pop()
        # ~ szJSON = aImageRecords[irand].GetJsonId(irand)
        # ~ dJAttr = json.loads(szJSON)
        # ~ print (dJAttr)
        # ~ ir = ImageRecord(dAttr = dJAttr)
        # ~ print(ir)
       
    #reset all sets of test records
    # ~ for i in (a1+a2+a3+a4+a5):
        # ~ aImageRecords[i].favorite = False
        # ~ aImageRecords[i].likes = 0
        # ~ aImageRecords[i].edited = None
        # ~ aImageRecords[i].last_played = None
    dtYesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    logging.debug(f"Found {len(GetEditedSinceIds(aImageRecords,dtYesterday))} edited")
        
    tSaveS = time.process_time()
    SaveIRcsv(mifcfg.image_records_file_read,aImageRecords,safe=True)
    tSave = time.process_time()
    logging.debug(f"Done saving [{tSave-tSaveS}]")
    
    tEnd = time.process_time()
    logging.debug(f"Elapsed Time:\t{tEnd-tStart}")
