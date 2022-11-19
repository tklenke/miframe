# app.py or app/__init__.py
from flask import Flask, render_template, send_file, jsonify, redirect, url_for, flash
import src.config as mifcfg
import datetime, time
import threading
import selector
import logging
import io
from PIL import Image, ImageTk, ImageFile


#-----------------START UP Tasks--------------------
app = Flask(__name__)
app.config.from_object('config')
app.config["DEBUG"]

# Now we can access the configuration variables via app.config["VAR_NAME"].
ImageFile.LOAD_TRUNCATED_IMAGES = True
logging.getLogger().setLevel(logging.DEBUG)

#Initiate Server Info
tStart = time.process_time()
dtStart = datetime.datetime.now()
#need this to flash messages
szMachineId = selector.GetMachineId()
app.secret_key = szMachineId

#Initiate Save Globals
aDirtyIds = []
dtLastSave = None

#load the selector
aImageRecords = selector.LoadIRcsv(mifcfg.image_records_file_read)
tLoad = time.process_time()
logging.debug(f"Read {len(aImageRecords)} image records in {(tLoad-tStart):.4f} seconds")
logging.debug(f"Shuffling image records")
aIdQueue = selector.Shuffle(aImageRecords)
tShuffle = time.process_time()
logging.debug(f"Done shuffling image records in {(tShuffle-tLoad):.4f} seconds")
aRecentImgIds = []

#make sure photo_directory ends in '/'
if mifcfg.photo_root_path[-1] != '/':
    szPhotoRoot = mifcfg.photo_root_path + '/'
else:
    szPhotoRoot = mifcfg.photo_root_path
logging.info(f"Photo Library at: {szPhotoRoot}")



#----------Main App--------------------
if __name__ == "__main__":
    #start main 
    app.run(host='0.0.0.0')




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
  

#-----------------RECURRING TASKS----------------------------
#starts with first request, then re-runs indefinately
@app.before_first_request
def activate_recurring_job():
    def run_job():
        while True:
            global dtLastSave, aDirtyIds
            if len(aDirtyIds) > 0:
                logging.debug(f"Save requested for {len(aDirtyIds)} ids")
                (nRecs, nFileSz) = selector.SaveIRcsv(mifcfg.image_records_file_read,aImageRecords,safe=True)
                dtLastSave = datetime.datetime.now()
                logging.info(f"Save completed. {nRecs} records {nFileSz} bytes at {dtLastSave}")
                aDirtyIds = []
            time.sleep(600)

    thread = threading.Thread(target=run_job)
    thread.start()

#-----------------ROUTES-------------------------------------
@app.route("/")
def home():
    aIds = aRecentImgIds[-10:]
    aIds.reverse()
    return render_template('home.html',page_title='Home',aids=aIds)
    
@app.route("/selectir")
def selectirj():
#select next image record and return json with index into aImageRecords
    global aIdQueue
    if len(aIdQueue) > 0:
        nId = aIdQueue.pop()
    else:
        aIdQueue = selector.Shuffle(aImageRecords)
        nId = aIdQueue.pop()
    aRecentImgIds.append(nId)
    aImageRecords[nId].last_played = datetime.datetime.now()
    dDict = aImageRecords[nId].__dict__
    dDict['id'] = nId
    return jsonify(dDict)

@app.route("/<string:machine_id>/selectirmid")
def selectirmidj(machine_id):
    return redirect(url_for('selectirj'))

#--------image routes----------------    
@app.route("/<int:img_id>/img")
def getimage(img_id):
    if img_id not in range(0,len(aImageRecords)):
        return make_response(render_template('error.html'), 404)
    fullpath = szPhotoRoot + aImageRecords[img_id].path
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
    
@app.route("/savenow")
def savenow():
    global dtLastSave, aDirtyIds
    (nRecs, nFileSz) = selector.SaveIRcsv(mifcfg.image_records_file_read,aImageRecords,safe=True)
    flash(f"Save completed. {nRecs} records {nFileSz} bytes")
    dtLastSave = datetime.datetime.now()
    logging.info(f"Save completed. {nRecs} records {nFileSz} bytes at {dtLastSave}")
    aDirtyIds = []
    return redirect(url_for('utilities'))
    

#-----client-server data exchange routes----------------
@app.route("/chksrvr")
def check_server():
    return ('',202)    

@app.route("/<string:machine_id>/getini")
def get_frame_ini(machine_id):
    dDict={}
    dDict['FRAME']={}
    dDict['FRAME']['machine_id']=machine_id
    return jsonify(dDict)
    
