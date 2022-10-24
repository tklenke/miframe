# app.py or app/__init__.py
from flask import Flask, render_template, send_file

app = Flask(__name__)
app.config.from_object('config')

# Now we can access the configuration variables via app.config["VAR_NAME"].
app.config["DEBUG"]

@app.route("/")
def home():
    return render_template('home.html')
    
@app.route("/img")
def image():
    fullpath = "/home/admin/Pictures/fallback/dscf0010.jpg"
    # ~ resp = app.make_response(open(fullpath).read())
    # ~ resp.content_type = "image/jpeg"
    return send_file(fullpath,"image/jpeg")    
    
if __name__ == "__main__":
   app.run(host='0.0.0.0')
