from tinydb import TinyDB, Query, where
from tinyrecord import transaction
from aescrypt import encrypt_file
import os

def enc():
	db = TinyDB('db\data.json')
	File = Query()
	files = db.search(File.enc == 'False')
	for f in files:
	    print('tmp/' + f['name'], f['password'])
	    encrypt_file(f['password'].encode('utf-8'), 'tmp/' + f['name'])

	    os.remove('tmp/' + f['name'])
	    enc_filename = f['name'] + '.enc'

	    with transaction(db) as tr:
	        tr.update({'name': enc_filename, 'password': 'None', 'enc': 'True'}, where('id') == f['id'])
