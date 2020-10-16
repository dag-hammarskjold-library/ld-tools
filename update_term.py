import logging
import argparse
import re
from pymongo import MongoClient
from dlx.config import Config as dlxConfig
from dlx.marc import DB, Auth, Query, Condition
from ld_sync import skos, tcode, mdu
from ld_sync.config import Config

# Init
logging.basicConfig(filename='logs/update.log', level=logging.DEBUG)
DB.connect(Config.connect_string)

def new_from_skos(skos_marc):
    new_tcode = tcode.mint()
    date_tag, date_code = dlxConfig.date_field
    skos_marc.set(date_tag, date_code, '19991231')
    skos_marc.set_008()
    skos_marc.set('035','a', new_tcode, address=["+"])
    logging.debug(f"New record to create from SKOS\n{skos_marc.to_mrk()}")

# Step 1: get arguments
parser = argparse.ArgumentParser(description='Update a Thesaurus term across existing systems.')
parser.add_argument('uri', metavar='uri', type=str)
parser.add_argument('--reindex', type=bool, default=False)
args = parser.parse_args()

# Step 2: Perform an update against metadata.un.org so we can get the SKOS
# This is usually skipped
if args.reindex:
    print("Will reindex metadata.un.org")

# Step 3: Get SKOS and make MARC from it
skos_marc = skos.to_marc(args.uri)
logging.debug(f'MARC generated from SKOS\n{skos_marc.to_mrk()}')

# Step 4: Is this an existing auth? If so, we'll merge in the SKOS output.
# If not, we need to create the auth record.
try:
    #raise AttributeError
    pref_label = skos_marc.get_value('150','a')
    query = Query(Condition('150', subfields={"a":  pref_label}))
    marc_auth = Auth.find_one(query.compile(), limit=1)
    logging.debug(f'MARC generated from record lookup\n{marc_auth.to_mrk()}')
    
    # Merge the skos_marc output into the existing record
    merged_marc = marc_auth.merge(skos_marc)
    logging.debug(f'Merged MARC record. Original MARC on the right, SKOS incoming\n{merged_marc.to_mrk()}')

    #merged_marc.commit()

except AttributeError:
    # This is a new term. Do we need to set 000, 001, and 008?
    # This works, but doesn't set 000, 001, and 008
    new_tcode = tcode.mint()
    skos_marc.set('035','a', new_tcode, address=["+"])
    logging.debug(f"New record to create from SKOS\n{skos_marc.to_mrk()}")
    #skos_marc.commit()
except:
    raise