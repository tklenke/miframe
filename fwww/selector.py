import src.config as config
import csv
import datetime, time
import logging
import random
logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')

#miframe specific includes
from src.mif import ImageRecord

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

#select a file
def SelectImg(aImgRecs):
    return (random.choice(aImgRecs))

#serve the file


#----------MAIN------------    
if __name__ == '__main__':
    tStart = time.process_time()
    
    logging.getLogger().setLevel(logging.DEBUG)
    
    aImageRecords = LoadIRcsv(config.image_records_file_read)
    logging.debug(f"Read {len(aImageRecords)} image records")

    for i in range(0,10):
        print(SelectImg(aImageRecords))
    
    tEnd = time.process_time()
    logging.debug(f"Elapsed Time:\t{tEnd-tStart}")
