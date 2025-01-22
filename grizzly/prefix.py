import re


common_prefixes = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'skos': 'http://www.w3.org/2004/02/skos/core#',
            'skosxl': 'http://www.w3.org/2008/05/skos-xl#',
            'mesh': 'http://id.nlm.nih.gov/mesh/2018/',
            'meshv': 'http://id.nlm.nih.gov/mesh/vocab#',
            'NALTconcept': 'http://lod.nal.usda.gov/nalt/Concept-',
            'NALTlabel': 'http://lod.nal.usda.gov/nalt/Label-',
            'prov': 'http://www.w3.org/ns/prov#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'dct': 'http://purl.org/dc/terms/'
           }

def replace_prefix(value, prefixes):
    if not isinstance(value, str):
        return value
    match = re.match(r'(^[a-zA-Z]*?):(?!/)', value)
    if match:
        prefix = match.groups()[0]
        if prefix in prefixes:
            return re.sub(prefix + ':', prefixes[prefix], value)
    return value


class Prefix:

    def __init__(self, iri):
        self.iri = iri

    def __getattr__(self, key):
        return self.iri + key

    def __getitem__(self, key):
        return self.iri + key
