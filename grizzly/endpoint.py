from uplink import Consumer, get, Path, Query, Header, Body, post, headers, response_handler, json, delete
from .parser import SPARQLParser
from .model import GraphModelBuilderSemantics, SelectQuery, ConstructQuery, UpdateQuery

formats_results= {
'csv': 'text/csv',
'json': 'application/sparql-results+json',
'xml': 'application/sparql-results+xml',
'binary': 'application/x-binary-rdf-results-table'
}

formats_graph = {
'json': 'application/rdf+json',
'xml': 'application/rdf+xml',
'binary': 'application/x-binary-rdf-results-table',
'json-ld': 'application/ld+json',
'turtle': 'text/turtle',
'n3': 'text/rdf+n3',
# 'n-triples': 'text/x-ntriples',
'n-quads': 'text/x-nquads',
'trix': 'application/trix',
'trig': 'application/x-trig'
}

def raise_for_status(response):
    if not response.ok:
        raise ConnectionError('HTTP %s: %s'%(response.status_code,response.text))
    else:
        return response

@response_handler(raise_for_status)
class RDF4JEndpoint(Consumer):

    def __init__(self, base_url, repository='', *args, **kwargs):
        if not repository and len(base_url.split('/repositories/')) == 2:
            base_url, repository = base_url.split('/repositories/')
        super().__init__(base_url=base_url, *args, **kwargs)
        self.repository = repository

    def query(self, query, format='json'):
        parsed_query = SPARQLParser().parse(query, semantics=GraphModelBuilderSemantics(), rule_name='query')
        query_type = type(parsed_query.body)
        if query_type is SelectQuery:
            try:
                format = formats_results[format]
            except:
                raise IOError('Select queries do not support "%s" as response format.'%format)
            return self.select_query(self.repository, query, format)
        elif query_type is ConstructQuery:
            try:
                format = formats_graph[format]
            except:
                raise IOError('Construct queries do not support "%s" as response format.'%format)
            return self.construct_query(self.repository, query, format)
        elif query_type is UpdateQuery:
            return self.update_query(self.repository, query)
        else:
            raise NotImplementedError('Query type "%s" not implemented yet.'%query_type)

    @get('/repositories/{repository}')
    def select_query(self, repository: Path('repository'), query: Query,
              format: Header('accept') = 'application/sparql-results+json'):
        pass

    @get('/repositories/{repository}')
    def construct_query(self, repository: Path('repository'), query: Query,
             format: Header('accept') = 'application/rdf+json'):
        pass

    @post('/repositories/{repository}/statements')
    def update_query(self, repository: Path('repository'), update: Query):
        pass

    def get_graph(self, graph, format='application/rdf+json'):
        if graph is 'default':
            return self.get_default_graph(self.repository, format)
        else:
            return self.get_named_graph(self.repository, graph, format)

    def post_graph(self, graph, data, format='application/rdf+json'):
        if graph is 'default':
            return self.post_default_graph(self.repository, data, format)
        else:
            return self.post_named_graph(self.repository, graph, data, format)

    def delete_graph(self, graph):
        if graph is 'default':
            return self.delete_default_graph(self.repository)
        else:
            return self.delete_named_graph(self.repository, graph)

    @get('/repositories/{repository}/rdf-graphs/service?default')
    def get_default_graph(self, repository: Path('repository'),
                  format: Header('accept') = 'application/rdf+json'):
        pass

    @post('/repositories/{repository}/rdf-graphs/service?default')
    def post_default_graph(self, repository: Path('repository'),
           data: Body, format: Header('content-type') = 'application/rdf+json'):
        pass

    @delete('/repositories/{repository}/rdf-graphs/service?default')
    def delete_default_graph(self, repository: Path('repository')):
        pass

    @get('/repositories/{repository}/rdf-graphs/service')
    def get_named_graph(self, repository: Path('repository'), graph: Query('graph'),
                  format: Header('accept') = 'application/rdf+json'):
        pass

    @post('/repositories/{repository}/rdf-graphs/service')
    def post_named_graph(self, repository: Path('repository'), graph: Query('graph'),
           data: Body, format: Header('content-type') = 'application/rdf+json'):
        pass

    @delete('/repositories/{repository}/rdf-graphs/service')
    def delete_named_graph(self, repository: Path('repository'), graph: Query('graph')):
        pass

    def list_graphs(self):
        return self._list_graphs(self.repository)

    @get('/repositories/{repository}/contexts')
    def _list_graphs(self, repository: Path('repository'),
                format: Header('accept') = 'application/sparql-results+json'):
        pass

    @get('/repositories')
    def list_repositories(self):
        pass

    def size(self):
        return self._repository_size(self.repository)

    @get('/repositories/{repository}/size')
    def _repository_size(self, repository: Path('repository')):
        pass


@response_handler(raise_for_status)
class SPARQLEndpoint(Consumer):

    def query(self, query, format='json'):
        parsed_query = SPARQLParser().parse(query, semantics=GraphModelBuilderSemantics(), rule_name='query')
        query_type = type(parsed_query.body)
        if query_type is SelectQuery:
            try:
                format = formats_results[format]
            except:
                raise IOError('Select queries do not support "%s" as response format.'%format)
            return self.select_query(query, format)
        elif query_type is ConstructQuery:
            try:
                format = formats_graph[format]
            except:
                raise IOError('Construct queries do not support "%s" as response format.'%format)
            return self.construct_query(query, format)
        elif query_type is Delete_insert_query:
            return self.update_query(query)
        else:
            raise NotImplementedError('Query type "%s" not implemented yet.'%query_type)

    @get('/sparql')
    def select_query(self, query: Query,
              format: Header('accept') = 'application/sparql-results+json'):
        pass

    @get('/sparql')
    def construct_query(self, query: Query,
             format: Header('accept') = 'application/rdf+json'):
        pass

    @post('/sparql')
    def update_query(self, update: Query,
             format: Header('content-type') = 'application/rdf+json'):
        pass

    @post('/sparql')
    def insert_data(self, data: Body,
            format: Header('content-type') = 'application/rdf+json'):
        pass

    # @get('/repositories')
    # def repositories(self):
    #     pass
    #
    # @get('/sparql')
    # def repository_size(self):
    #     pass
