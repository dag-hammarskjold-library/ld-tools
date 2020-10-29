import json
import requests
import sys
from pymongo import MongoClient
from ld_sync.config import Config

client = MongoClient(Config.connect_string)
db = client[Config.dbname]
ref_coll = "thesaurus_codes"

def populate():
    thesaurus_codes = db[ref_coll].find()
    for res in thesaurus_codes:
        endpoint = f'http://metadata.un.org/thesaurus/{res["field_035"]}'
        try:
            uri = requests.get(endpoint).json()['uri']
            try:
                print(f'{res["field_035"]} {res["field_001"]} {uri} {res["field_150"]}')
                db[ref_coll].update_one({"field_001": res["field_001"]}, {"$set": {"uri": uri}})
            except KeyError:
                pass
        except json.decoder.JSONDecodeError:
            pass
        