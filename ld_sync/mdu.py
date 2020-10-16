import requests
import json

def get_term(uri):
    headers = {'accept': 'application/ld+json'}
    term_json = requests.get(uri, headers=headers)
    term = json.loads(term_json.text)
    return term

def get_ttl(uri):
    headers = {'accept': 'text/turtle'}
    ttl = requests.get(uri, headers=headers)
    return ttl

def update_metadata_un_org(uri, thesaurus_endpoint, api_key):
    data = {
        'key': api_key,
        'uri': uri
    }
    try:
        this_r = requests.post(thesaurus_endpoint, data=data)
    except:
        raise

    term = get_term(uri)

    for predicate in ['skos:broader', 'skos:narrower', 'skos:related', 'skos:inScheme']:
        try:
            this_rels = term[predicate]
            if isinstance(this_rels, list):
                for rel in this_rels:
                    update_metadata_un_org(rel["@id"], thesaurus_endpoint, api_key)
            else:
                update_metadata_un_org(this_rels["@id"], thesaurus_endpoint, api_key)
        except KeyError:
            pass
        except:
            raise