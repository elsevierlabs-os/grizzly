from .endpoint import RDF4JEndpoint, SPARQLEndpoint
from .factories import read_json
from .prefix import common_prefixes
from .graph import Graph

endpoints = {
'rdf4j': RDF4JEndpoint,
'sparql': SPARQLEndpoint
}


class Repository:
    '''This class represents a graph store repository as an abstraction over a
    REST API. The API is designed to mirror the API of the local `Graph` class.
    All methods take instances of `Graph` as arguments and return instances of
    `Graph` or `Table`. Initialize with the `base_url`
    (e.g. `http://localhost:7200`). In the case of an RDF4J endpoint either
    select the repository by providing it as `repository_name` or included it in
    the `base_url` (e.g. `http://localhost:7200/repositories/example`).
    Additionally `custom_prefixes` can be supplied which
    will be used to generate prefix defintions in queries. For authentication
    you can provide `username` and `password`.
    '''

    def __init__(self, base_url, repository_name='', custom_prefixes={},
                 username='', password='', api='rdf4j'):
        self.prefixes = common_prefixes.copy()
        self.prefixes.update(custom_prefixes)
        self.endpoint = endpoints[api](base_url=base_url,
                        repository=repository_name, auth=(username, password))

    def query(self, query):
        '''Query the repository with a SPARQL query. Automatically adds known
        prefix defintions to the query. Currently supported are `CONSTRUCT`,
        `SELECT`, `DELETE` and `INSERT` queries. Returns a `Graph` instance or a
        `Table` instance depending on the type of the query.
        '''
        graph = Graph(prefixes=self.prefixes)
        parsed_query =  graph.parse(query)
        graph._prologue(parsed_query.prologue)
        standard_prolog = '\n'.join([f'prefix {prefix}:<{iri}>'
                            for prefix, iri in graph.prefixes.items()])
        parseinfo = parsed_query.body.parseinfo
        query = standard_prolog + '\n' + query[parseinfo.pos:parseinfo.endpos]
        response = self.endpoint.query(query=query)
        result = read_json(response.content, custom_prefixes=self.prefixes)
        return result

    def insert(self, graph, name):
        '''Inserts `graph` into the repository. `graph` should be a `Graph`
        instance. The graph will be inserted into `name` which can
        either be a named graph or `'default'`. Returns `True` if succesful.
        '''
        if type(graph) is not Graph:
            data = Graph(graph).to_json()
        else:
            data = graph.to_json()
        response = self.endpoint.post_graph(data=data, graph=name)
        return self

    def get_graph(self, name):
        '''Gets an entire graph from the repository and returns it as `Graph`
        instance. The graph `name` can either be a named graph or `'default'`.
        '''
        response = self.endpoint.get_graph(graph=name)
        result = read_json(response.content, custom_prefixes=self.prefixes)
        return result

    def list_graphs(self):
        '''Returns a `Table` containing all named graphs in the repository.
        '''
        response = self.endpoint.list_graphs()
        result = read_json(response.content)
        return result

    def size(self):
        '''Returns the number of triples in the repository.
        '''
        response = self.endpoint.size()
        return int(response.content)
