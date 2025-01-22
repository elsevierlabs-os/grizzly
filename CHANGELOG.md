# Release notes

## Version 0.3.1

- added a Cython based basic turtle parser
- fix an import statement to work with pandas version > 23.4
- fix JSON deserialization if "xml:lang" key is used for language strings
- fix test for NaNs in deserialization with pandas function
- fix an issue of attempting to decode an already decoded graph

## Version 0.3.0

- added a `Repository` class that makes it easy to work with a remote graph store
- added more documentation
- added faster (de)serialization to RDF/JSON
- improve typing and serialization of type information
- implement LIMIT solution modifier
- added implementations for SPARQL built-ins`LANG` and `DATATYPE`
- pass any `DataFrame` like object to `graph.insert` and `graph.delete`, decoding and encoding is taken care of automatically

## Version 0.2.1

- initialize `Graph` or `Table` with any data that works with `DataFrame`, data is automatically encoded into integers
- support IN and NOT IN operators with expression lists
- bug fixes around typing and delete queries

## Version 0.2.0

- instantiate an empty graph by simply calling without arguments: `gz.Graph()`
- blocks of literal values supported
- property paths with Kleene plus supported
- typed strings with language tags
- better serialization to turtles (with language tags)
- SPARQLWrapper replaced with custom wrapper to allow for larger uploads
- load from and to remote graph store

## Version 0.1.0

- load graphs from files containing triples or from remote graph stores
- contains parsers generated with Tatsu
- run basic SPARQL queries:
  - SELECT and CONSTRUCT queries
  - updates with DELETE and INSERT
  - UNION, FILTER, BIND, OPTIONAL are implemented
  - literals, prefixed and relative IRIs are implemented
  - property paths with alternatives, sequences and inversions work
- following restrictions apply:
  - result depends on position of OPTIONAL clause in group, should be independent
  - FILTER and BIND don't work with variables of containing clauses
- run queries using GraphFrames query patterns:
  - empty nodes and edges are not allowed yet
- basic serialization to triples, not conforming to standards!
