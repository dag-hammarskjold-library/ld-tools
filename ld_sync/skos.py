import requests
import json
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import SKOS 
from dlx.marc import Auth, Datafield, DB
from ld_sync.tcode import mint
from ld_sync.mdu import get_term
from ld_sync.config import Config

DB.connect(Config.connect_string)

EU = Namespace('http://eurovoc.europa.eu/schema#')
DC = Namespace('http://purl.org/dc/elements/1.1/')
DCTERMS = Namespace("http://purl.org/dc/terms/")
UNBIST = Namespace('http://metadata.un.org/thesaurus/')
SDG = Namespace('http://metadata.un.org/sdg/')
SDGO = Namespace('http://metadata.un.org/sdg/ontology#')

lang_tags_map = {
    'ar': {
        'prefLabel': '995',
        'altLabel': '495',
        'scopeNote': '935',
        'note': '695',
    },
    'zh': {
        'prefLabel': '996',
        'altLabel': '496',
        'scopeNote': '936',
        'note': '696',
    },
    'en': {
        'prefLabel': '150',
        'altLabel': '450',
        'scopeNote': '680',
        'note': '670',
    },
    'fr': {
        'prefLabel': '993',
        'altLabel': '493',
        'scopeNote': '933',
        'note': '693',
    },
    'ru': {
        'prefLabel': '997',
        'altLabel': '497',
        'scopeNote': '937',
        'note': '697',
    },
    'es': {
        'prefLabel': '994',
        'altLabel': '494',
        'scopeNote': '934',
        'note': '694',
    }
}

def populate_graph(graph=None, uri=None):
    if graph is None:
        graph = Graph()
    g = Graph()
    g.bind('skos', SKOS)
    g.bind('eu', EU)
    g.bind('dc', DC)
    g.bind('dcterms', DCTERMS)
    g.bind('unbist', UNBIST)
    g.bind('sdg', SDG)
    g.bind('sdgo', SDGO)

    headers = {'accept': 'text/turtle'}
    ttl = requests.get(uri, headers=headers).text

    try:
        graph.parse(data=ttl, format="turtle")
        for triple in graph:
            g.add(triple)
    except:
        raise

    return g

def to_marc(uri):
    g = populate_graph(graph=None, uri=uri)

    auth = Auth()
    #auth.set("035", "a", uri)
    field = Datafield(tag='035', record_type='auth').set('a', uri)
    auth.fields.append(field)
    
    for f035 in g.objects(URIRef(uri), DCTERMS.identifier):
        if "lib-thesaurus" in f035:
            pass
        else:
            #auth.set('035', 'a', f035, address=["+"])
            field = Datafield(tag='035', record_type='auth').set('a', f035)
            auth.fields.append(field)

    auth.set_values(
        ('040','a', 'NNUN'),
        ('040','b', 'eng'),
        ('040','f', 'unbist')
    )

    # Two types of broader terms: one forms the dot-notated hierarchy, e.g., 01.01.00
    # The other forms broader terms in the usual sense (i.e, to other proper terms)
    for f072a in g.objects(URIRef(uri), SKOS.broader):
        bc = f072a.split('/')[-1]
        if len(bc) == 6:
            n = 2
            chunks = [bc[i:i+n] for i in range(0, len(bc), n)]
            dotted = ".".join(chunks)
            field = Datafield(tag='072', record_type='auth')
            field.ind1 = '7'
            field.ind2 = ' '
            field.set('a', dotted)
            field.set('2', 'unbist')
            auth.fields.append(field)
        else:
            populate_graph(graph=g, uri=f072a)
            for f550 in g.objects(URIRef(f072a), SKOS.prefLabel):
                if f550.language == 'en':
                    try:
                        #auth.set('550', 'w', 'g', {'address': ["+"]})
                        #auth.set('550','a', f550)
                        datafield = Datafield(tag="550", record_type="auth").set('w', 'g').set('a', f550, auth_control=True)
                        auth.fields.append(datafield)
                    except:
                        print(f"Could not assign {f550} to 550 as a broader term")
                        pass

    # related terms go in 550 with only $a
    for f550 in g.objects(URIRef(uri), SKOS.related):
        populate_graph(graph=g, uri=f550)
        for preflabel in g.objects(URIRef(f550), SKOS.prefLabel):
            if preflabel.language == 'en':
                    try:
                        #auth.set('550', 'w', 'g', address=["+"])
                        #auth.set('550','a', preflabel, address=["+"])
                        datafield = Datafield(tag="550", record_type="auth").set('a', preflabel, auth_control=True)
                        auth.fields.append(datafield)
                        
                    except:
                        print(f"Could not assign {preflabel} to 550 as a related term")
                        pass


    # narrower terms go in 550 with $w = h
    for f550 in g.objects(URIRef(uri), SKOS.narrower):
        populate_graph(graph=g, uri=f550)
        for preflabel in g.objects(URIRef(f550), SKOS.prefLabel):
            if preflabel.language == 'en':
                    try:
                        #auth.set('550', 'w', 'h', {'address': ["+"]})
                        #auth.set('550','a', preflabel)
                        datafield = Datafield(tag="550", record_type="auth").set('w', 'h').set('a', preflabel, auth_control=True)
                        auth.fields.append(datafield)
                    except:
                        print(f"Could not assign {preflabel} to 550 as a narrower term")
                        pass
    
    # English pref labels go in 150
    for f150 in g.objects(URIRef(uri), SKOS.prefLabel):
        field = Datafield(tag=lang_tags_map[f150.language]['prefLabel'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f150)
        auth.fields.append(field)

    # English alt labels go in 450
    for f450 in g.objects(URIRef(uri), SKOS.altLabel):
        field = Datafield(tag=lang_tags_map[f450.language]['altLabel'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f450)
        auth.fields.append(field)

    # English scope notes go in 680
    for f680 in g.objects(URIRef(uri), SKOS.scopeNote):
        field = Datafield(tag=lang_tags_map[f680.language]['scopeNote'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f680)
        auth.fields.append(field)

    # 688? 

    # English general/source notes go in 670, other langs in 933-937
    for f670 in g.objects(URIRef(uri), SKOS.note):
        field = Datafield(tag=lang_tags_map[f670.language]['note'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f670)
        auth.fields.append(field)
    
    return auth

def merged(left, right):
    # We keep what's in the left document and overwrite whatever is in the right document
    auth = Auth()
    auth.id = left.id

    # find all the tags that are in the right (SKOS)
    skos_tags = right.get_tags()

    # and all the tags in the left (original MARC)
    original_tags = left.get_tags()

    # copy the original, because we're gonna subtract
    keep_tags = original_tags

    # Subbtract the skos tags from the original tags and store them in what we're keeping
    for st in skos_tags:
        keep_tags.remove(st)

    # process the left side of the record (what we're keeping)
    for tag in keep_tags:
        this_fields = left.get_fields(tag)
        for field in this_fields:
            auth.fields.append(field)

    # process the right side of the record (the incoming values from the SKOS)
    for tag in skos_tags:
        this_fields = right.get_fields(tag)
        for field in this_fields:
            auth.fields.append(field)
    
    return auth