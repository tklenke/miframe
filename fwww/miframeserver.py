# app.py or app/__init__.py
from flask import Flask, render_template, send_file
import src.config as mifcfg
import selector
import logging

app = Flask(__name__)
app.config.from_object('config')

# Now we can access the configuration variables via app.config["VAR_NAME"].
app.config["DEBUG"]

#load the selector
logging.getLogger().setLevel(logging.DEBUG)

aImageRecords = selector.LoadIRcsv(mifcfg.image_records_file_read)
logging.debug(f"Read {len(aImageRecords)} image records")
#make sure photo_directory ends in '/'
if mifcfg.photo_root_path[-1] != '/':
    szPhotoRoot = mifcfg.photo_root_path + '/'
else:
    szPhotoRoot = mifcfg.photo_root_path

@app.route("/")
def home():
    return render_template('home.html')
    
@app.route("/getimg")
def image():
    oImgRec = selector.SelectImg(aImageRecords)
    fullpath = szPhotoRoot + oImgRec.path
    return send_file(fullpath,"image/jpeg")    
    
if __name__ == "__main__":
   app.run(host='0.0.0.0')
