from ld_sync.config import Config

db = Config.db_client[Config.dbname]

def mint():
    res = db.thesaurus_codes.find().sort("field_035", -1).limit(1)
    max_code = res[0]['field_035']
    str_code = max_code.replace("T","")
    int_code = int(str_code)
    new_int_code = int_code + 1
    new_code = "T" + str(new_int_code).rjust(7,"0")

    return new_code

def save(tcode, auth_id, label, uri):
    try:
        #print(tcode, auth_id, label, uri)
        db.thesaurus_codes.insert_one({
            "field_035": tcode,
            "field_001": auth_id,
            "field_150": label,
            "uri": uri
        })
    except:
        raise

ref_coll = "thesaurus_codes"

def get_all():
    results = db.thesaurus_codes.find().sort("uri")
    return_results = []
    for res in results:
        try:
            this_r = {
                'field_035': res["field_035"],
                'field_001': res["field_001"],
                'field_150': res["field_150"],
                'uri': res["uri"]
            }
            if this_r not in return_results:
                return_results.append(this_r)
        except KeyError:
            next
    return return_results