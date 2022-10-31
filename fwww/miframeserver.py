# app.py or app/__init__.py
from flask import Flask, render_template, send_file, jsonify
import src.config as mifcfg
import datetime, time
import selector
import logging
import io
from PIL import Image, ImageTk, ImageFile

app = Flask(__name__)
app.config.from_object('config')

# Now we can access the configuration variables via app.config["VAR_NAME"].
app.config["DEBUG"]
ImageFile.LOAD_TRUNCATED_IMAGES = True
logging.getLogger().setLevel(logging.DEBUG)

#load the selector
tStart = time.process_time()
aImageRecords = selector.LoadIRcsv(mifcfg.image_records_file_read)
tLoad = time.process_time()
logging.debug(f"Read {len(aImageRecords)} image records in {tLoad-tStart} seconds")
logging.debug(f"Shuffling image records")
aIdQueue = selector.Shuffle(aImageRecords)
tShuffle = time.process_time()
logging.debug(f"Done shuffling image records in {tShuffle-tLoad} seconds")


#make sure photo_directory ends in '/'
if mifcfg.photo_root_path[-1] != '/':
    szPhotoRoot = mifcfg.photo_root_path + '/'
else:
    szPhotoRoot = mifcfg.photo_root_path
logging.info(f"Photo Library at: {szPhotoRoot}")

aRecentImgIds = []

#-------functions
  


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
    aImageRecords[nId].last_played = datetime.datetime.now().timestamp()
    dDict = aImageRecords[nId].__dict__
    dDict['id'] = nId
    return jsonify(dDict)
    
@app.route("/<int:img_id>/img")
def getimage(img_id):
    if img_id in range(0,len(aImageRecords)):
        fullpath = szPhotoRoot + aImageRecords[img_id].path
        return send_file(fullpath,"image/jpeg")
    else:
        return make_response(render_template('error.html'), 404)
        
@app.route("/<int:img_id>/editshow")
def editshow(img_id,action=None):
    return render_template('edit.html',page_title=f"Edit img:{img_id}",nId=img_id)
    
@app.route("/<int:img_id>_<int:width>x<int:height>/thumb")
def getthumb(img_id,width,height):
    if img_id in range(0,len(aImageRecords)):
        fullpath = szPhotoRoot + aImageRecords[img_id].path
        with Image.open(fullpath) as img:
            #rotate first    
            if aImageRecords[img_id].orientation == 3:
                img.rotate(180)
            elif aImageRecords[img_id].orientation == 6:
                img.rotate(270)
            elif aImageRecords[img_id].orientation == 8:
                img.rotate(90)
            
            img.thumbnail((width,height))
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG', quality=70)
            img_io.seek(0)
            return send_file(img_io, mimetype='image/jpeg')
    else:
        return make_response(render_template('error.html'), 404)

         
     
    
if __name__ == "__main__":
   app.run(host='0.0.0.0')
