
def open_as_unicode(file):
    with open(file, 'r') as f:
        string = f.read()
    return string


def open_as_bytes(file):
    with open(file, 'rb') as f:
        string = f.read()
    return string

file = 'OS.nt'


%timeit open_as_unicode(file)
%timeit open_as_bytes(file)
unicode_string = open_as_unicode(file)
bytes_string = open_as_bytes(file)

import pyximport; pyximport.install(reload_support=True, language_level=3, build_in_temp=False)

import turtle_parser
%timeit -n 1 -r 1 p = turtle_parser.parse(bytes_string)

import cy_turtle_parser1
%timeit -n 1 -r 1 p = cy_turtle_parser1.parse(bytes_string)

import cy_turtle_parser2
%timeit -n 1 -r 1 p = cy_turtle_parser2.parse(bytes_string)

import cy_turtle_parser3
%timeit p = cy_turtle_parser3.parse(bytes_string)

import cy_turtle_parser4
%timeit p = cy_turtle_parser4.parse(bytes_string)

import cy_turtle_parser5
%timeit p = cy_turtle_parser5.parse(bytes_string)

import cy_turtle_parser6
%timeit p = cy_turtle_parser6.parse(bytes_string)

import cy_turtle_parser6b
%timeit p = cy_turtle_parser6b.parse(bytes_string)

import cy_turtle_parser6c
%timeit p = cy_turtle_parser6c.parse(bytes_string)

import cy_turtle_parser6d
%timeit p = cy_turtle_parser6d.parse(bytes_string)

import cy_turtle_parser7
%timeit p = cy_turtle_parser7.parse(bytes_string)

import cy_turtle_parser8
%timeit p = cy_turtle_parser8.parse(bytes_string)

bytes_string = b'#@prefix :<http://bla> .\n <http://concept> a <http://concept> .'

p = cy_turtle_parser8.parse(bytes_string)
p
i = 17260074
bytes_string[i-20:i+20]


import grizzly as gz

def load_from_file(file):
    with open(file, 'rb') as f:
        string = f.read()
    triples, vertices, codes, prefixes, baseIRI = cy_turtle_parser8.parse(string)
    graph = gz.Graph(data=triples, vertices=vertices, codes=codes,
                     prefixes=prefixes, baseIRI=baseIRI, encoded=True)
    return graph

%timeit graph = load_from_file('OS.ttl')
graph.decode()

s = graph.head(20).decode().iloc[10,1]
type(s)
graph.prefixes

%timeit r = graph.query('''select * {?c a skos:Concept . ?c skosxl:prefLabel ?l . ?l skosxl:literalForm ?s . filter(strstarts(?s, "Econ"))}''')
len(r)

type(graph.sample(10).decode().iloc[0,2])

r = [i for t in p for i in t]
%timeit s = sorted(r)

counter = 0
res = [0]*len(s)
state = None

for i, item in enumerate(s):
    if item != state:
        counter += 1
    res[i] = counter
    state = item

res


%timeit graph = gz.Graph(p)

x = graph.decode()
x.iloc[0,0]

def graph_from_file(file):
    bytes_string = open_as_bytes(file)
    triples = cy_turtle_parser6d.parse(bytes_string)
    return triples

%timeit -n 1 -r 1  p = graph_from_file('OS.nt')
%timeit -n 1 -r 1  p = graph_from_file('OE.nt')

p = graph_from_file('OS.nt')

# string = rb'<http://data.elsevier.com/vocabulary/OmniScience/Concept-250231336> <http://www.w3.org/2004/02/skos/core#scopeNote> "The EES keyword for this was Brain Areas. \"Areas\" was changed to \"Part\" because there are named areas in the brain, such as association areas and Brodmann areas, that are not what the EES keyword includes as its children. It would be misleading to retain \"Areas\" in the label." .'

p = graph_from_file('OE.nt')
p
len(p)

string = rb'''
@prefix
<http:/Concept-192553644> <http://#type> <http://core#Concept> .
<http://Concept-192553644> <http:#type> <http://Omni_Med_Dentistry> .
<http://Concept-210628428> <http:#type> <http:/02/skos/core#Concept> ;
<http:#type> <http://Omni_FoodScience> .
<http://Label-215551918> <http://#type> 'something\" here'^^sdfs .
'''

p = cy_turtle_parser6.parse(string)

%timeit -n 1 -r 1 parse(unicode_string)
%timeit -n 1 -r 1 parse(bytes_string)

print(bytes_string[66415490:66415720])

x = bytes_string[66415290:66415720]

with open('snippet.txt', 'wb') as f:
    f.write(x)

|import pyximport; pyximport.install(build_in_temp=False)

import cyparser5
%timeit -n 1 -r 1 cyparser5.parse(bytes_string)

import cyparser6
%timeit cyparser6.parse(bytes_string)

import cyparser7
%timeit cyparser7.parse(bytes_string)

%timeit cyparser7.parse(open_as_bytes(file))

triples


%timeit cyparser7.parse(open_as_bytes('OE.nt'))

%timeit open_as_bytes('OE.nt')
