import os
import json
from flask import Flask, request, url_for, render_template, send_from_directory
from werkzeug import secure_filename
from datetime import datetime
from tinydb import TinyDB, Query
from tinyrecord import transaction
import uuid
import hashlib
import aescrypt
import crypter


db = TinyDB('db\data.json')
File = Query()
UPLOAD_FOLDER = 'tmp/'
ALLOWED_EXTENSIONS = set(['txt', 'jpg', 'jpeg', 'png'])


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def stamp():
    d = datetime.now()
    timestamp = str(d.day) + str(d.minute) + str(d.hour) + str(d.second) + str(d.microsecond) + '__'
    return timestamp


def random_id_gen():
    random_id = str(uuid.uuid4())
    random_id = ''.join(random_id.split('-'))
    return random_id


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route("/", methods=['GET', 'POST'])
def index():
    random_id = None
    if request.method == 'POST':
        file = request.files['file']
        password = request.form['pass']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = stamp()
            filename = timestamp + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            f = open('tmp/' + filename, 'rb')
            line = f.readlines()
            magic = str(line[0][0:20])

            random_id = random_id_gen()
            file_url = url_for('files') + random_id

            m = hashlib.md5()
            m.update(password.encode('utf-8'))
            passhash = str(m.hexdigest())
            with transaction(db) as tr:
                tr.insert({'name': filename, 'id': random_id, 'password': passhash, 'enc': 'False', 'magic': magic})
            f.close()
            crypter.enc()

            return render_template('main.html', file_url=file_url)
    return render_template('main.html', file_url=random_id)


@app.route("/files/<file_id>")
@app.route("/files/")
def files(file_id):
    if request.method == 'POST':
        result = db.search(File.id == file_id)
        return request.url

    else:
        result = db.search(File.id == file_id)
        file_name = result[0]['name']
        return render_template('down.html', file_name=file_name, file_id = file_id)


@app.route("/download", methods=['GET', 'POST'])
def download():
    password = request.form['pass']
    file_id = request.form['file_id']
    m = hashlib.md5()
    m.update(password.encode('utf-8'))
    passhash = str(m.hexdigest())
    result = db.search(File.id == file_id)

    res = aescrypt.decrypt_file(passhash, "tmp/" + result[0]['name'], result[0]['magic'])
    filename = result[0]['name'][:-4]
    if res:
        print("Verified")
        return send_from_directory(directory='tmp', filename=filename, as_attachment=True)
    else:
        os.remove(filename)
        return "Password Wrong.."


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
