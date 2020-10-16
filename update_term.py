import logging
import argparse
import re
from pymongo import MongoClient
from dlx.marc import DB, Auth, Query, Condition
from ld_sync import skos, tcode, mdu
from ld_sync.config import Config

logging.basicConfig(filename='logs/update.log', level=logging.DEBUG)
#db_client = MongoClient(Config.connect_string)
DB.connect(Config.connect_string)

# Step 1: get arguments
parser = argparse.ArgumentParser(description='Update a Thesaurus term across existing systems.')
parser.add_argument('uri', metavar='uri', type=str)
args = parser.parse_args()

# Step 2: Get SKOS and make MARC from it
skos_marc = skos.to_marc(args.uri)
# Step 2a: Is there a tcode?
this_tcode = None
for identifier in skos_marc.get_values('035','a'):
    if re.match("^T.*",identifier):
        this_tcode = identifier

if this_tcode is None:
    this_tcode = tcode.mint()
    skos_marc.set('035','a',this_tcode, address=["+"])

logging.debug(f'MARC generated from SKOS\n{skos_marc.to_mrk()}')

# Step 3: Is this an existing auth?
try:
    pref_label = skos_marc.get_value('150','a')
    query = Query(Condition('150', subfields={"a":  pref_label}))
    marc_auth = Auth.from_query(query.compile(), limit=1)
    
    # Merge the skos_marc output into the existing record
    merged_marc = marc_auth.merge(skos_marc)
except AttributeError:
    # This is a new term.
    pass
except:
    raise