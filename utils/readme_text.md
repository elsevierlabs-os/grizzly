# Grizzly

Grizzly is a [Pandas](http://pandas.pydata.org/) based package working with RDF graphs.

{TOC}

## Release notes

Please check the [release notes](CHANGELOG.md) for detailed changes by version.

## Installation

Grizzly is a ready to install Python package. You need to have Python 3 installed (not tested with Python 2) and the packages listed in the requirements file.

```sh
pip install -r requirements.txt
```

### Direct installation to simply use Grizzly

You can install Grizzly directly from this repository. On the command line type

```sh
pip install git+https://github.com/elsevierlabs-os/grizzly.git
```

To upgrade Grizzly to a new version run:

```sh
pip install --upgrade grizzly
```

### Install Grizzly for development

Clone the repository to a convenient location for you.

```sh
git clone https://github.com/elsevierlabs-os/grizzly.git
```

Then install Grizzly without transferring it to the Python site-packages directory. This way any change to the source files is immediately reflected when you use the package.

```sh
cd grizzly
pip install -e .
```

## General use

![overview](overview.png)

Load triples from a CSV file:

```python
import grizzly as gz
graph = gz.read_csv('filename.csv')
```

Load a graph from a remote graph store (replace the text between asterisks):

```python
creds = {'base_url': 'http://localhost:8000',
         'name': 'example',
         'username': **username**,
         'password': **password**}
store = gz.Repository(**creds)
graph = store.query('select * {?s ?p ?o .} limit 100')
```


Run a SPAQRL query:

```python
graph.query('''
select ?sub
where {
  ?sub ?pre ?obj .
}
''')
```

Run a query using the GraphFrames DSL:

```python
graph.find('(a)-[b]->(c);(c)-[d]->(e)').filter('b = skos:broader')
```

You can run update queries directly. This returns a new graph with the updates:

```python
updated_graph = graph.query('''
delete {
  ?parent skos:narrower ?child.
}
insert {
  ?parent skos:broader ?child .
}
where {
  ?parent skos:narrower ?child.
}
''')
```

It is also possible to delete or insert triples that had previously been generated through a CONSTRUCT query:

```python
new_triples = graph.query('''
construct {
  ?parent skos:broader ?child .
}
where {
  ?parent skos:narrower ?child.
}
''')
updated_graph = graph.insert(new_triples)
```

Serialize the graph to plain triples that can be uploaded to a graphstore:
```python
triples = graph.to_triples()
```


## Tutorials


- [Get started](examples/grizzly-demo.ipynb)

