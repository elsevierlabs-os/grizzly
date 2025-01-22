import tatsu

with open('./SPARQL.ebnf') as f:
    SPARQLgrammar = f.read()

with open('./GFDSL.ebnf') as f:
    GFDSLgrammar = f.read()

with open('../grizzly/parser.py', 'w') as f:
    SPARQLparser = tatsu.to_python_sourcecode(SPARQLgrammar, name='SPARQL')
    f.write(SPARQLparser)
    GFDSLparser = tatsu.to_python_sourcecode(GFDSLgrammar, name='GFDSL')
    f.write(GFDSLparser[532:])

with open('../grizzly/model.py', 'w') as f:
    model = tatsu.to_python_model(SPARQLgrammar, name='Graph')
    f.write(model)
