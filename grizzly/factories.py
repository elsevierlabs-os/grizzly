import pandas as pd
import numpy as np
import json
from .graph import Graph
from .table import Table
from .types import URI, json_to_typed
from .endpoint import RDF4JEndpoint
from .cy_turtle_parser import parse as parse_turtle


def read_csv(string, *args, custom_prefixes={}, keep_default_na=False, **kwargs):
    '''Reads a file or string in CSV format and returns a `Graph`. You can supply
    `custom_prefixes` that should be taken into account.
    '''
    # string = _load_file_or_string(string)
    data = pd.read_csv(string, *args, keep_default_na=keep_default_na, **kwargs)
    return Table(data, prefixes=custom_prefixes)

def read_turtle(string, custom_prefixes={}):
    '''Reads a file or string in ttl format and returns a `Graph`. You can supply
    `custom_prefixes` that should be taken into account.
    '''
    string = _load_file_or_string(string, binary=True)
    triples, vertices, codes, prefixes, baseIRI = parse_turtle(string)
    graph = Graph(data=triples, vertices=vertices, codes=codes,
                  prefixes=prefixes, baseIRI=baseIRI, encoded=True)
    return graph

def read_ntriples(string, custom_prefixes={}):
    '''Reads a file or string of N-triples and returns a `Graph`. This might be
    slow as it uses the query parser at the moment.You can supply
    `custom_prefixes` that should be taken into account.
    '''
    string = _load_file_or_string(string)
    graph = Graph(prefixes=custom_prefixes)
    parsed_triples = pd.DataFrame(
                     [(graph.term(triple.sub, ast=True),
                       graph.term(triple.pre[0][0].term, ast=True),
                       graph.term(triple.obj, ast=True))
                      for triple in graph.parse(string, rule_name='patterns')]
                      )
    return Graph(parsed_triples, prefixes=custom_prefixes)

def read_remote(query, endpointURL, repository, custom_prefixes={}, username='', password=''):
    '''Queries a SPARQL endpoint at `endpointURL` with `query`. The preferred
    way at the moment is to instead call a query on a `Repository` instance.
    '''
    endpoint = RDF4JEndpoint(base_url=endpointURL, auth=(username, password))
    response = endpoint.query(query=query, repository=repository)
    result = read_json(response.content, custom_prefixes=custom_prefixes)
    return result

def read_json(string, custom_prefixes={}):
    '''Reads a file or graph store response in the JSON format. If it is
    RDF/JSON it returns a typed Graph, if it has the MIME type
    'application/sparql-results+json' it return a typed DataFrame. You can
    supply `custom_prefixes` that should be taken into account.
    '''
    string = _load_file_or_string(string)
    deserial = json.loads(string)

    if 'head' in deserial:
        columns = deserial['head']['vars']
        results = deserial['results']['bindings']
        df = pd.DataFrame(results, columns=columns).applymap(json_to_typed)
        return Table.from_df(df, custom_prefixes)
    else:
        triples = [(subject, predicate, object)
                    for subject, predicates in deserial.items()
                    for predicate, objects in predicates.items()
                    for object in objects]
        df = pd.DataFrame(triples, columns=['s', 'p', 'o'])
        df['s'] = df['s'].apply(URI)
        df['p'] = df['p'].apply(URI)
        df['o'] = df['o'].apply(json_to_typed)
        return Graph.from_df(df, custom_prefixes)

def _load_file_or_string(string, binary=False):
    try:
        if binary:
            with open(string, 'rb') as file:
                string = file.read()
        else:
            with open(string, encoding='utf-8') as file:
                string = file.read()
    except:
        if binary and isinstance(string, str):
            string = string.encode(encoding='utf-8')
    return string
