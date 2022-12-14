# app.py or app/__init__.py
from flask import Flask, render_template, send_file, jsonify, redirect, url_for, flash, make_response
from flask import appcontext_tearing_down
import configparser
import datetime, time
import threading
import logging
import io
import os
import multiprocessing
import subprocess
from PIL import Image, ImageTk, ImageFile
#MiFrame Modules
import selector
from librarian import DatabaseMaintenance, ImportPhotos
from src.mif import CheckPathSlash, BackupFile, SaveIni
from mpwrapper import MifProcess
#for testing
from mpwrapper import TBuildList, TAddList, TUpdateList, T2xAddList
g_a = TBuildList()
nCounter = 0
#end testing


        

#-----------------START UP Tasks--------------------
logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')
### Load MiFrame Configuration
cfg = configparser.ConfigParser()
g_szIniPath = os.getenv('MIFRAME_INI', '/home/admin/projects/miframe/fwww/miframe.ini')
if not os.path.exists(g_szIniPath):
    logging.critical(f"Can't find config file {g_szIniPath}")
    exit()
cfg.read(g_szIniPath)
g_bDirtyIni = False

### Set Up Logging
logging.info(f"log debug [{cfg.getboolean('LEVEL','debug')}]")
logging.info(f"log www [{cfg.getboolean('LEVEL','wwwlog')}]")

if cfg.getboolean('LEVEL','debug'):
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.ERROR)
### web server logs    
flasklog = logging.getLogger('werkzeug')
if cfg.getboolean('LEVEL','wwwlog'):
    flasklog.setLevel(logging.INFO)
else:
    flasklog.setLevel(logging.ERROR)
    

### Misc Flags set
ImageFile.LOAD_TRUNCATED_IMAGES = True

### Initiate Server Info
tStart = time.process_time()
dtStart = datetime.datetime.now()


### Initiate Save Globals
aDirtyIds = []
dtLastSave = None

### load the selector
aImageRecords = selector.LoadIRcsv(cfg.get('PATHS','image_records_file'))
tLoad = time.process_time()
logging.debug(f"Read {len(aImageRecords)} image records in {(tLoad-tStart):.4f} seconds")
logging.debug(f"Shuffling image records")
aIdQueue = selector.Shuffle(aImageRecords)
tShuffle = time.process_time()
logging.debug(f"Done shuffling image records in {(tShuffle-tLoad):.4f} seconds")
aRecentImgIds = []

# make sure photo_directory ends in '/'
szPhotoRoot = CheckPathSlash(cfg.get('PATHS','photo_root_path'))
logging.info(f"Photo Library at: {szPhotoRoot}")

### Initialize multiprocessing object
mp = MifProcess()


#-------functions--------------------------------------------
def GetServerStats():
    dStats = {}
    dStats['Machine Id'] = szMachineId
    dStats['Number Image Records'] = str(len(aImageRecords))
    dStats['Recs in Queue'] = str(len(aIdQueue))
    dStats['Server Start Time'] = str(dtStart)
    #ratio of processing seconds to seconds of elapsed uptime
    fSecsProcessTime = time.process_time() - tStart
    fSecsElapsedTime = (datetime.datetime.now() - dtStart).total_seconds()
    dStats['Seconds Process Time'] = f"{fSecsProcessTime:.4f}"
    dStats['Seconds Elapsed Time'] = f"{fSecsElapsedTime:.4f}"   
    dStats['Server Utilization'] = f"{(( fSecsProcessTime / fSecsElapsedTime )*100.):.2f}"
    dStats['Last Data Save'] = str(dtLastSave)
    dStats['Records to be Saved'] = str(len(aDirtyIds))
    dStats['Photo Root'] = szPhotoRoot
    dStats[''] = 'TBA'
    
    return (dStats)
    
def TransferData():
    global mp, g_a, aImageRecords, aDirtyIds         
    if mp.DataExists('a'): 
        g_a = mp.GetArray('a')
    if mp.DataExists('IRs'):
        b = True 
        aImageRecords = mp.GetArray('IRs')
        #put one record in to force save
        aDirtyIds.append(0)   

def GetMachineOrientation(mid):
    global g_bDirtyIni
    if cfg.has_option(mid,'display_type'):
        return (cfg.get(mid,'display_type'))
    logging.info(f"Setting machine {mid} orientation to both")
    cfg[mid] = {}
    cfg.set(mid,'flip_after_millisecs','60000')
    cfg.set(mid,'display_type','both')
    g_bDirtyIni = True
    return ('both')


#----------Main App--------------------
app = Flask(__name__)
# Now we can access the configuration variables via app.config["VAR_NAME"].
app.config.from_object('config')
app.config["DEBUG"]
#need this to flash messages
szMachineId = selector.GetMachineId()
app.secret_key = szMachineId

if __name__ == "__main__":
    #start main 
    print("miframeserver __main__")
    app.run(host='0.0.0.0')


#-----------------RECURRING TASKS----------------------------
#starts with first request, then re-runs indefinately
@app.before_first_request
def activate_recurring_job():
    def run_job():
        while True:
            global dtLastSave, aDirtyIds, g_bDirtyIni, g_szIniPath, mp, g_a
            logging.debug(f"Running recurring job")
            if len(aDirtyIds) > 0:
                nRecs = 0
                nFileSz = 0
                logging.debug(f"Save requested for {len(aDirtyIds)} ids")
                # ~ (nRecs, nFileSz) = selector.SaveIRcsv(cfg.get('PATHS','image_records_file'),aImageRecords,safe=True)
                dtLastSave = datetime.datetime.now()
                logging.info(f"Save completed. {nRecs} records {nFileSz} bytes at {dtLastSave}")
                aDirtyIds = []
            #in case user moves away from long running process and does not allow to complete
            #clean it up.
            if mp.process is not None:
                if mp.IsAlive():
                    logging.debug(f"mp process alive")
                else:
                    logging.debug(f"mp process not alive. blocking")
                    mp.Close()
                    TransferData()
                    logging.debug(f"mp process not alive. released")
            ## if config needs to be updated then save it out
            if g_bDirtyIni:
                logging.debug(f"Saving ini file {g_szIniPath}")
                g_bDirtyIni = False
                SaveIni(cfg,g_szIniPath)
            logging.debug(f"Done recurring job")
            time.sleep(60)

    thread = threading.Thread(target=run_job)
    thread.start()

    

#-----------------ROUTES-------------------------------------
@app.route("/")
def home():
    aIds = aRecentImgIds[-10:]
    aIds.reverse()
    return render_template('home.html',page_title='Home',aids=aIds)

@app.route("/<string:machine_id>/selectirmid")
def selectirmidj(machine_id):
#select next image record and return json with index into aImageRecords
    global aIdQueue
    # Get orientation for this machine
    orientation = GetMachineOrientation(machine_id)
    # for each image in queue if matches orientation then return
    nId = None
    while (nId is None):
        for i in range(0,len(aIdQueue)):
            logging.debug(f"o:{orientation} Id:{aIdQueue[i]} IsPortrait:{aImageRecords[aIdQueue[i]].IsPortrait()}")
            if (orientation == 'both') or \
               (orientation == 'portrait' and aImageRecords[aIdQueue[i]].IsPortrait()) or \
               (orientation == 'landscape' and aImageRecords[aIdQueue[i]].IsLandscape()):
                nId = aIdQueue[i]
                aIdQueue.pop(i)
                break                
        # if get to end of queue then shuffle all records and try again
        if nId is None:
            aIdQueue = selector.Shuffle(aImageRecords)
    aRecentImgIds.append(nId)
    aImageRecords[nId].last_played = datetime.datetime.now()
    dDict = aImageRecords[nId].__dict__
    dDict['id'] = nId
    return jsonify(dDict)
    
#--------image routes----------------    
@app.route("/<int:img_id>/img")
def getimage(img_id):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    fullpath = szPhotoRoot + aImageRecords[img_id].path
    if not os.path.exists(fullpath):
        logging.error(f"could not find image {fullpath}")
        return make_response(render_template('error.html'), 404)
    return send_file(fullpath,"image/jpeg")

@app.route("/<int:img_id>_<int:width>x<int:height>/thumb")
def getthumb(img_id,width,height):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    fullpath = szPhotoRoot + aImageRecords[img_id].path

    with Image.open(fullpath) as img:
        #rotate first    
        if aImageRecords[img_id].orientation in (3,4):
            iRot = img.rotate(180,expand=True)
        elif aImageRecords[img_id].orientation in (5,6):
            iRot = img.rotate(270,expand=True)
        elif aImageRecords[img_id].orientation in (7,8):
            iRot = img.rotate(90,expand=True)
        else:
            iRot = img
        
        iRot.thumbnail((width,height))
        img_io = io.BytesIO()
        iRot.save(img_io, 'JPEG', quality=70)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')

#----edit routes--------
@app.route("/<int:img_id>/edit")
def edit(img_id):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    return render_template('edit.html',page_title=f"Edit img:{img_id}",\
        nId=img_id,dImgInfo=aImageRecords[img_id].__dict__)

@app.route("/<int:img_id>/replay")
def replay(img_id):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    
    #put it on the top of the queue, only once
    if len(aIdQueue) == 0:
        aIdQueue.append(img_id)
    elif aIdQueue[-1] != img_id:
        aIdQueue.append(img_id)
    return redirect(url_for('edit',img_id=img_id))

@app.route("/<int:img_id>/rotate")
def rotate(img_id):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    aImageRecords[img_id].RotateCW()
    #put on queue to save
    aDirtyIds.append(img_id)
    return redirect(url_for('edit',img_id=img_id))
                
@app.route("/<int:img_id>/thumbsup")
def thumbsup(img_id):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    aImageRecords[img_id].ThumbsUp()
    #put on queue to save
    aDirtyIds.append(img_id)
    return redirect(url_for('edit',img_id=img_id))
            
@app.route("/<int:img_id>/thumbsdown")
def thumbsdown(img_id):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    aImageRecords[img_id].ThumbsDown()
    #put on queue to save
    aDirtyIds.append(img_id)
    return redirect(url_for('edit',img_id=img_id))
                
@app.route("/<int:img_id>/favorite")
def favorite(img_id):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    aImageRecords[img_id].Favorite()  
    #put on queue to save
    aDirtyIds.append(img_id)  
    return redirect(url_for('edit',img_id=img_id))
                
@app.route("/<int:img_id>/block")
def block(img_id):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    aImageRecords[img_id].Block()
    #put on queue to save
    aDirtyIds.append(img_id) 
    flash(f"Image: {img_id} Blocked")
    return redirect(url_for('neighbors',img_id=img_id))

#-----utility routes----------------
@app.route("/utilities")
def utilities():
    dStats = GetServerStats()
    return render_template('utilities.html',page_title='Utilities',dstats=dStats)
    
@app.route("/favorites")
def favorites():
    aIds = selector.GetFavoriteIds(aImageRecords)
    return render_template('list.html',page_title='Favorites',aids=aIds)

@app.route("/liked")
def liked():
    aIds = selector.GetLikedIds(aImageRecords,3)
    aIds += selector.GetLikedIds(aImageRecords,2)
    aIds += selector.GetLikedIds(aImageRecords,1)
    return render_template('list.html',page_title='Thumbs Up / Liked',aids=aIds)

@app.route("/blocked")
def blocked():
    aIds = selector.GetBlockedIds(aImageRecords)
    return render_template('list.html',page_title='Blocked',aids=aIds)

@app.route("/<int:img_id>/neighbors")
def neighbors(img_id):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    aIds = []
    nLower = img_id - 7
    nUpper = img_id + 7
    if nLower < 1:
        nLower = 1
    if nUpper > len(aImageRecords):
        nUpper = len(aImageRecords)
    for i in range(nLower,nUpper):
        aIds.append(i)
    return render_template('list.html',page_title=f"Neighbors:{img_id}",aids=aIds)
    
@app.route("/backupdb")
def backup_db():
    szBUPath = CheckPathSlash(cfg.get('PATHS','miframe_etc_path')) + 'backup/'    
    szFile = BackupFile(cfg.get('PATHS','image_records_file'),szBUPath)
    flash(f"Backed up database to {szFile}")
    return redirect(url_for('utilities'))

@app.route("/savenow")
def savenow():
    global dtLastSave, aDirtyIds
    (nRecs, nFileSz) = selector.SaveIRcsv(cfg.get('PATHS','image_records_file'),aImageRecords,safe=True)
    flash(f"Save completed. {nRecs} records {nFileSz} bytes")
    dtLastSave = datetime.datetime.now()
    logging.info(f"Save completed. {nRecs} records {nFileSz} bytes at {dtLastSave}")
    aDirtyIds = []
    return redirect(url_for('utilities'))
    
@app.route("/reloaddb")
def reload_db():
    aImageRecords = selector.LoadIRcsv(cfg.get('PATHS','image_records_file'))
    flash(f"Reloaded database. {len(aImageRecords)} records")
    logging.debug(f"Read {len(aImageRecords)} image records")
    aDirtyIds = []
    return redirect(url_for('utilities'))
    
@app.route("/systemshutdown")
def shutdown():
    subprocess.run("shutdown -h 0", shell=True, check=True)
    return "Shutting down!"

#-----client-server data exchange routes----------------
@app.route("/chksrvr")
def check_server():
    return ('',202)    

@app.route("/<string:machine_id>/getini")
def get_frame_ini(machine_id):
    dDict={}
    dDict['NETWORK']={}
    return jsonify(dDict)

@app.route("/<string:machine_id>/fallbacks")
def get_frame_fallbacks(machine_id):
    #get list of favorite ids
    aIds = selector.GetFavoriteIds(aImageRecords)
    #returns dict of [ImageRecId]:[path]
    dDict = {}
    for i in aIds:
        dDict[i] = aImageRecords[i].path
    return jsonify(dDict)

#-----photo librarian routes----------------
@app.route("/rundbmx")
def run_db_mx():
    global mp
    if mp.IsAlive():
        return make_response(render_template('error.html',error_msg='Cannot start process twice.' ), 400)
    logging.debug(f"len array {len(aImageRecords)}")
    pIRs = mp.NewList('IRs',aImageRecords)
    logging.debug(f"{type(pIRs)}")
    mp.SetFunction(DatabaseMaintenance,"Database Maintenance")
    mp.SetArgs((pIRs,len(pIRs)))
    mp.Start()
    return render_template('process_status.html',page_title='Database Maintenance',\
        description='Database Maintenance', status_url=url_for('status_mp'))
        
@app.route("/importphotos")
def import_photos():
    global mp
    if mp.IsAlive():
        return make_response(render_template('error.html',error_msg='Cannot start process twice.' ), 400)
    pIRs = mp.NewList('IRs',aImageRecords)
    logging.debug(f"{type(pIRs)}")
    mp.SetFunction(ImportPhotos,"Import Photos")
    mp.SetArgs((pIRs,len(pIRs)))
    mp.Start()
    return render_template('process_status.html',page_title='Import Photos',\
        description='Import Photos', status_url=url_for('status_mp'))
        
@app.route("/statusmp")
def status_mp():
    global mp, g_a, aImageRecords
    d={}
    # get the message text from the queue
    msg = ""
    while (True):
        msg_next = mp.Get()
        if msg_next:
            if msg_next[:len('[H]')] == '[H]':
                mp.description = msg_next[len('[H]'):]
            elif msg_next[:len('[R]')] == '[R]':
                mp.result_msg += f"{msg_next[len('[R]'):]}\n"
                msg += f"\t[{msg_next[len('[R]'):]}]\n"
            else:
                msg += f"\t[{msg_next}]\n"
        else:
            break
    if mp.IsAlive():
        if msg == "":
            msg = "\tWorking...\n"
        d['statustxt'] = f"Latest Status:\n{msg}"
        d['done'] = False
    else:
        mp.Close()
        TransferData()
        if msg != "":
            d['statustxt'] = f"Final Status:\n\t\n{msg}\n\tDone."
        else:
            d['statustxt'] = f"Final Status:\n\tDone."
        d['done'] = True
    d['description'] = mp.description
    d['results'] = mp.result_msg
    logging.debug(f"len array {len(g_a)} {len(aImageRecords)}")
    return jsonify(d)

#-----testing routes----------------
@app.route("/<int:num_secs>//pausebeforeresponse")
def pause_before_response(num_secs):
    time.sleep(num_secs)
    return redirect(url_for('utilities'))

@app.route("/testmp")
def test_mp():
    global mp, g_a
    if mp.IsAlive():
        return make_response(render_template('error.html',error_msg='Cannot start process twice.' ), 400)
    logging.debug(f"len array {len(g_a)}")
    pa = mp.NewList('a',g_a)
    mp.SetFunction(T2xAddList,"2x Add to List")
    mp.SetArgs((pa,.5))
    mp.Start()
    return render_template('process_status.html',page_title='TAdd',description=mp.description,\
        status_url=url_for('status_mp'))

@app.route("/geta")
def get_a():
    global g_a
    d={}
    d['msg']=f"len array {len(g_a)}"
    d['a'] =g_a
    logging.debug(f"len array {len(g_a)}")
    return jsonify(d)

