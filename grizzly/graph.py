import pandas as pd
import numpy as np
import operator
from functools import reduce
import html
import re
from . import model
from . import types
from .base import Base, directly_queryable
from .endpoint import RDF4JEndpoint
from .utils import concat
from .types import typed_to_json
import json

def Table(*args, **kwargs):
    from .table import Table
    return Table(*args, **kwargs)


class Graph(Base):
    '''This class represents an RDF graph in memory.
    '''

    def __init__(self, data=None, *args, **kwargs):
        if data is None:
            data = {'sub': [], 'pre': [], 'obj': []}
        super().__init__(data, *args, **kwargs)
        assert(len(self.columns) == 3)
        self.columns = ['sub', 'pre', 'obj']

    def find(self, query_string):
        '''Query the graph with the motif patterns used in GraphFrame, like e.g.
        `graph.find('(sub)-[pre]->(obj)')`. Not fully implemented at the moment.
        '''
        query = self.parse(query_string, rule_name='query', parser='GFDSL')
        return self.where(query, ast=True)

    def query(self, query_string):
        '''Query the graph with a SPARQL query. Currently supported are `CONSTRUCT`,
        `SELECT`, `DELETE` and `INSERT` queries. Returns a `Graph` instance or a
        `Table` instance depending on the type of the query.
        '''
        query = self.parse(query_string, rule_name='query')
        self._prologue(query.prologue)
        return self._body(query.body)

    def _prologue(self, query):
        for declaration in query:
            if type(declaration) is model.PrefixDeclaration:
                self.prefixes[declaration.prefix] = declaration.iri.value
            elif type(declaration) is model.BaseDeclaration:
                self.base = declaration.iri

    def _body(self, query):
        if type(query) is model.SelectQuery:
            return (self.where(query.where_clause.ast, ast=True)
                        .modify_solution(query.solution_modifier)
                        .select(query.select_clause, ast=True))
        elif type(query) is model.ConstructQuery:
            return (self.where(query.where_clause.ast, ast=True)
                        .construct(query.construct_clause, ast=True))
        elif type(query) is model.UpdateQuery:
            result = self.copy()
            for request in query.ast:
                subset = self.where(request.where_clause.ast, ast=True)
                if request.delete_clause:
                    delete_update = subset.construct(request.delete_clause, ast=True)
                    result = result.delete(delete_update)
                if request.insert_clause:
                    insert_update = subset.construct(request.insert_clause, ast=True)
                    result = result.insert(insert_update)
            return result
        else:
            raise NotImplementedError('The type "%s" is not implemented yet'%type(query))

    @directly_queryable(rule_name='patterns')
    def where(self, query):
        '''Returns a `Table`
        '''
        query = query.ast if type(query) is model.Group else query
        if type(query) is model.SelectQuery:
            return self._body(query)
        if len(query) == 0:
            return pd.DataFrame({})

        results_list = []
        filters = []
        for pattern in query:
            if type(pattern) is model.Optional:
                result = self.where(pattern.ast, ast=True)
                results_list = merge(results_list, result, how='left')
            elif type(pattern) is model.Minus:
                result = concat([r.copy() for r in results_list], sort=True)
                result['temp_index'] = np.arange(0, len(result))
                minus = self.where(pattern.ast, ast=True)
                to_drop = result.merge(minus)
                results_list = [result[~result['temp_index']
                                      .isin(to_drop['temp_index'])]
                                .drop(columns='temp_index')]
            elif type(pattern) is model.Union:
                left = self.where(pattern.left, ast=True)
                right = self.where(pattern.right, ast=True)
                result = concat([left.copy(), right.copy()], sort=True)
                results_list = merge(results_list, result)
            elif type(pattern) is model.Group:
                result = self.where(pattern, ast=True)
                results_list = merge(results_list, result)
            elif type(pattern) is model.Triple:
                result = self.triple(pattern, ast=True)
                results_list = merge(results_list, result)
            elif type(pattern) is model.Bind:
                result = concat([r.copy() for r in results_list], sort=True)
                decoded = result.decode()
                name = pattern.variable.name
                value = decoded.expression(pattern.expression, ast=True)
                result[name] = self.encode(value)
                results_list = [result]
            elif type(pattern) is model.Filter:
                filters.append(pattern)
            elif type(pattern) is model.Data_block:
                variables = [variable.name for variable in pattern.variables]
                values = [[self.term(value, ast=True, encode=True)
                           for value in tuple] for tuple in pattern.values_]
                result = Table(values, encoded=True,
                               columns=variables).copy_metadata(self)
                results_list = merge(results_list, result)

        result = concat([r for r in results_list], sort=True)
        if filters:
            decoded = result.decode().astype('object')
            masks = []
            for filter in filters:
                print(type(filter.ast))
                if type(filter.ast) is model.ExistsGroup:
                    exists_group = filter.ast
                    existance = type(exists_group.predicate) is model.Exists
                    triples = self.where(exists_group).assign(temp_exists=True)
                    if len(triples) == 0:
                        existing = pd.Series([False]*len(result), index=result.index)
                    else:
                        existing = result.merge(triples, how='left')['temp_exists']
                    mask = existing if existance else ~existing
                else:
                    mask = decoded.expression(filter.ast, ast=True)
                masks.append(mask)

            mask = reduce(operator.__and__, masks)
            result = result.loc[mask]

        return result

    @directly_queryable(rule_name='triple')
    def triple(self, query):
        result = self.to_table()
        constraints = {}
        if type(query.sub) is not model.Variable:
            constraints['sub'] = self.term(query.sub, encode=True, ast=True)
        if type(query.obj) is not  model.Variable:
            constraints['obj'] = self.term(query.obj, encode=True, ast=True)
        if type(query.pre) is not model.Variable:
            result = self._property_path(query.pre, constraints)
        else:
            result = result.constrain(constraints, constraints.keys())

        for part in ['sub', 'pre', 'obj']:
            query_part = getattr(query, part)
            if type(query_part) is model.Variable:
                result = result.rename(columns={part: query_part.name})
            elif part != 'pre':
                result = result.drop(columns=part)

        duplicate_cols = result.columns[result.columns.duplicated()]
        if len(duplicate_cols) == 1:
            result = result.loc[result[duplicate_cols].iloc[:,0] ==
                             result[duplicate_cols].iloc[:,1], ~result.columns.duplicated()]
        return result

    def _property_path(self, query, constraints):
        result = [self._path_sequence(subexpr, constraints) for subexpr in query]
        return concat(result, sort=True)

    def _path_sequence(self, query, constraints):
        if query[0].modifier == '+':
            sequent = self._path_item(query[0], {})
            result = sequent.constrain(constraints, ['sub'])
            results = [sequent]
            sequent = sequent.rename(columns={'sub': 'temp_query_col'})
            while True:
                result = result.rename(columns={'obj': 'temp_query_col'})
                result = result.merge(sequent).drop(columns='temp_query_col')
                if len(result) == 0:
                    break
                else:
                    results.append(result)
            sequent = concat(results).drop_duplicates()
        else:
            sequent = self._path_item(query[0], {})

        if len(query) > 1:
            result = sequent.constrain(constraints, ['sub'])
            for subexpr in query[1:]:
                new_constraint = result[['obj']].rename(columns={'obj': 'sub'})
                if subexpr.modifier == '+':
                    sequent = self._path_item(subexpr, {}).rename(columns={'sub': 'temp_query_col'})
                    result = sequent.constrain(constraints, ['sub'])
                    results = [sequent]
                    sequent = sequent.rename(columns={'sub': 'temp_query_col'})
                    while True:
                        result = result.rename(columns={'obj': 'temp_query_col'})
                        result = result.merge(sequent).drop(columns='temp_query_col')
                        if len(result) == 0:
                            break
                        else:
                            results.append(result)
                    result = concat(results)
                else:
                    sequent = self._path_item(subexpr, new_constraint)
                    result = result.rename(columns={'obj': 'temp_query_col'})
                    sequent = sequent.rename(columns={'sub': 'temp_query_col'})
                    result = result.merge(sequent).drop(columns='temp_query_col')
        else:
            result = sequent
        result = result.constrain(constraints, ['sub', 'obj'])
        return result

    def _path_item(self, query, constraint):
        inverted = {'sub': 'obj', 'obj': 'sub'}
        graph = self.rename(columns=inverted) if query.inverse else self.copy()
        # target = graph if constraint is None else constraint.merge(graph)

        if type(query.term) is model.Resource:
            pre = graph.term(query.term, encode=True, ast=True)
            return graph[graph['pre'] == pre].drop(columns='pre')
        else:
            return graph._property_path(query.term, constraint)

    def delete(self, triples, name=''):
        '''Deletes `triples` from the graph. `triples` must be a `DataFrame` or
        of a subclassed class with three columns.
        '''
        encoded_triples = self.get_encoded_triples(triples)
        result = self.copy()
        result['temp_index'] = np.arange(0, len(result))
        to_drop = result.merge(encoded_triples)
        return (result[~result['temp_index'].isin(to_drop['temp_index'])]
                        .drop(columns='temp_index').to_graph())

    def insert(self, triples, name=''):
        '''Adds `triples` to the graph. `triples` must be a `DataFrame` or of a
        subclassed class with three columns.
        '''
        encoded_triples = self.get_encoded_triples(triples)
        return concat([self, encoded_triples])

    def get_graph(self, name=''):
        return self

    def get_encoded_triples(self, triples):
        if not isinstance(triples, pd.DataFrame):
            raise TypeError(f'''You have to pass a DataFrame like object, not a\
                                {type(triples)}!''')
        elif len(triples.columns) != 3:
            raise TypeError(f'''You have to pass a DataFrame like object with 3\
            columns, not with {len(triples.columns)} columns!''')
        vertices = getattr(triples, 'vertices', [])
        encoded = getattr(triples, 'encoded', None)
        if encoded is None:
            triples = self.encode(Graph(triples).decode())
        elif not encoded or self.vertices != vertices:
            decoded = triples.decode() if encoded else triples
            triples = self.encode(decoded)
        else:
            triples = triples.copy()
        triples.columns = self.columns
        return triples

    def to_table(self):
        return Table(self, encoded=True).copy_metadata(self)

    def to_triples(self):
        decoded = self.decode()
        sub = decoded['sub'].apply(format_col)
        pre = decoded['pre'].apply(format_col)
        obj = decoded['obj'].apply(format_col)
        triples = '\n'.join(sub + ' ' + pre + ' ' + obj +' .')
        return triples

    def to_turtle(self, filename):
        decoded = self.decode()
        sub = decoded['sub'].apply(format_col)
        pre = decoded['pre'].apply(format_col)
        obj = decoded['obj'].apply(format_col)
        with open(filename, mode='w', encoding='utf-8') as f:
            turtle = '\n'.join(sub + ' ' + pre + ' ' + obj +' .')
            f.write(turtle)

    def to_json(self, filename=None):
        '''Serializes the graph to RDF/JSON. Returns a string if no `filename`
        is given, otherwise save the result as file.
        '''
        sorted_graph = self.sort_values(by=['sub', 'pre', 'obj']).decode()

        sub = sorted_graph['sub'].values
        pre = sorted_graph['pre'].values
        obj = list(sorted_graph['obj'].apply(typed_to_json).values)

        current_sub = 0
        current_pre = 0
        current_obj = 0

        i = 0
        subjects = {}
        while i < len(sorted_graph):
            current_sub = sub[i]
            predicates = {}
            while i < len(sorted_graph) and sub[i] == current_sub:
                current_pre = pre[i]
                j = i
                while i < len(sorted_graph) and sub[i] == current_sub and pre[i] == current_pre:
                    i += 1
                predicates.update({current_pre: obj[j:i]})
            subjects.update({current_sub: predicates})

        if filename is None:
            return json.dumps(subjects)
        else:
            with open(filename, 'w') as f:
                json.dump(subjects, f)

    def to_property_graph(self, filename=None, property_names={}, directed=False, multigraph=False, graph={}):

        property_names = {self.term(k): v for k,v in property_names.items()}

        sorted_graph = self.sort_values(by=['sub', 'pre', 'obj']).decode()
        rdf_type = self.term('a')
        URIs = sorted_graph.obj.apply(lambda x: type(x) is types.URI)
        isRdfType = sorted_graph.pre == rdf_type

        relations = sorted_graph[URIs&~isRdfType]
        properties = sorted_graph[~URIs|isRdfType]

        sub = properties['sub'].values
        pre = properties['pre'].values
        obj = properties['obj'].values

        current_sub = 0
        i = 0
        nodes = []
        while i < len(properties):
            current_sub = sub[i]
            node = {'id': current_sub}
            while i < len(properties) and sub[i] == current_sub:
                node.update({property_names.get(pre[i], pre[i]): obj[i]})
                i += 1
            nodes.append(node)

        links = [{'source': source, 'has_type': relation, 'target': target}
                 for source, relation, target in
                 zip(relations['sub'].values, relations['pre'].values, relations['obj'].values)]


        result = {'directed': directed, 'multigraph': multigraph,
                  'graph': graph, 'nodes': nodes, 'links': links}

        if filename is None:
         return json.dumps(result)
        else:
         with open(filename, 'w') as f:
             json.dump(result, f)

    def to_remote(self, endpointURL, repository, graph, username=None, password=None):
        data = self.to_json()
        endpoint = RDF4JEndpoint(base_url=endpointURL, auth=(username, password))
        response = endpoint.insert_data(data=data, repository=repository,
                                        graph=graph)
        return response

def merge(df_list, df, how='inner'):
    for i, result in enumerate(df_list):
        if any([c in result.columns for c in df.columns]):
            merged = result.merge(df, how=how)
            del df_list[i]
            return merge(df_list, merged)
    df_list.append(df)
    return df_list

def format_col(x):
    valuetype = type(x)
    if valuetype is types.URI:
        return '<' + x + '>'
    elif valuetype is types.LangStr:
        return '"%s"@%s'%(re.sub(r'"', r'\"', x), x.lang)
    elif valuetype is types.TypedStr:
        return '"%s"^^<%s>'%(re.sub(r'"', r'\"', x), x.datatype)
    elif valuetype in [int, float]:
        return str(x)
    else:
        return '<' + x + '>' if x.startswith('http') else '"%s"^^<http://www.w3.org/2001/XMLSchema#string>'%re.sub(r'"', r'\"', x)
