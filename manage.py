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

def create_term(args):
    print(f'Creating from {args.uri}')
    if args.reindex:
        print("Will reindex metadata.un.org")
    pass

def update_term(args):
    logging.debug(f'Updating: uri={args.uri}, id={args.id}')

    # Step 1: Reindex metadata.un.org and Elasticsearch, if specified
    if args.reindex:
        print("Will reindex metadata.un.org")

    # Step 2: Get SKOS from the URI location and make MARC from it
    skos_marc = skos.to_marc(args.uri)
    logging.debug(f'MARC generated from SKOS\n{skos_marc.to_mrk()}')

    # Step 3: Get MARC from the authority id
    marc_auth = Auth.find_one({'_id': int(args.id)})
    logging.debug(f'{args.id} found\n{marc_auth.to_mrk()}')

    # Step 4: Merge the two records, importing the SKOS to the original MARC
    merged_marc = marc_auth.merge(skos_marc)
    logging.debug(f'Merged record, with original MARC receving updates from the SKOS\n{merged_marc.to_mrk()}')

    # Step 5: Make sure the resulting merge has a tcode. Mint one if necessary.
    this_tcode = None
    save_tcode = False
    for identifier in merged_marc.get_values('035','a'):
        if re.match("^T.*", identifier):
            this_tcode = identifier
    if this_tcode is None:
        this_tcode = tcode.mint()
        merged_marc.set('035','a', this_tcode, address=["+"])
        save_tcode = True

    # Step 6: Save the record to the database.
    merged_marc.commit()

    # Step 7: Save the tcode to the thesaurus_codes collection
    if save_tcode:
        tcode.save(this_tcode, args.id, merged_marc.get_value('150','a'), args.uri)

# Step 1: Set up argument parsing and get arguments
parser = argparse.ArgumentParser(description='Create or update a Thesaurus term across existing systems.')
subparsers = parser.add_subparsers(title='subcommands')
create = subparsers.add_parser('create')
update = subparsers.add_parser('update')

create.add_argument('uri', metavar='uri', type=str)
# Note: when creating a new term, we aren't skipping the reindex in metadata.un.org and Elasticsearch
create.set_defaults(func=create_term)

update.add_argument('uri', metavar='uri', type=str)
update.add_argument('id', help='The id/001 of an existing authority.')
update.add_argument('--reindex', type=bool, default=False)
update.set_defaults(func=update_term)

args = parser.parse_args()
args.func(args)