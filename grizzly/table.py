import pandas as pd
import numpy as np
from pandas.core.groupby import DataFrameGroupBy
from . import model
from .base import Base, directly_queryable
from .utils import concat


def Graph(*args, **kwargs):
    from .graph import Graph
    return Graph(*args, **kwargs)


class Table(Base):

    @directly_queryable('select_group')
    def select(self, query):
        selection = query.selection
        if type(selection) is model.All:
            result = self.copy()
        else:
            result = self[[]].copy()
            for column in selection:
                if type(column) is model.Variable:
                    result[column.name] = self[column.name]
                else:
                    col = self.decode().expression(column.expression, ast=True)
                    encoded = result.encode(col)
                    result[column.variable.name] = encoded
        if query.modifier is not None:
            return result.drop_duplicates()
        else:
            return result

    @directly_queryable('construct_group')
    def construct(self, query):
        frames = []
        for triple in query:
            data = {}
            for part in ['sub', 'pre', 'obj']:
                query_part = getattr(triple, part)
                values = self.term(query_part, encode=True, ast=True)
                data[part] = values
            frame = (Table(data, encoded=True)
                       .copy_metadata(self)
                       .dropna()
                       .astype('int32')
                       .drop_duplicates()
                    )
            frames.append(frame)
        triples = concat(frames).drop_duplicates()
        return triples.to_graph()

    def modify_solution(self, query):
        result = self.copy()
        if query.groupby_clause:
            group_on = []
            print(query)
            for condition in query.groupby_clause:
                if type(condition) is model.Variable:
                    group_on.append(condition.name)
                else:
                    raise NotImplementedError('grouping on %s not yet implemented'%condition)
            result = result.decode().groupby(group_on)
        if query.orderby_clause:
            orders = [False if type(entry.order) is model.Desc else True for entry in query.orderby_clause]
            variables = [entry.variable.name for entry in query.orderby_clause]
            result = result.sort_values(by=variables, ascending=orders)
        if query.limit_clause:
            limit = int(query.limit_clause.value)
            result = result.head(limit)
        return result

    def groupby(self, *args, **kwargs):
        grouped = super().groupby(*args, **kwargs)
        return Grouped(grouped, self)#.copy_metadata(self)

    def sort_columns(self, col_a, col_b):
        result = self.copy()
        n = len(result)
        a = result[col_a].values
        b = result[col_b].values
        for i, (a_element, b_element) in enumerate(zip(a, b)):
            if a_element > b_element:
                a[i] = b_element
                b[i] = a_element
        return result

    def to_graph(self):
        return Graph(self, encoded=True).copy_metadata(self)



class Grouped:

    def __init__(self, grouped, table):
        self.grouped = grouped
        self.table = table

    def __getattribute__(self, key):
        if key in ['select', 'grouped', 'table']:
            return super().__getattribute__(key)
        else:
            return getattr(self.grouped, key)

    def __getitem__(self, key):
        return self.grouped[key]

    def select(self, query):
        selection = query.selection
        if type(selection) is model.All:
            raise KeyError('cannot select all on grouped result')
        else:
            index = []
            results = []
            for i, group in self.grouped:
                index.append(i)
                group = Table(group, encoded=True).copy_metadata(self.table)
                result = {}
                for column in selection:
                    if type(column) is model.Variable:
                        raise KeyError
                        # result[column.name] = group[column.name]
                    else:
                        col = group.expression(column.expression, ast=True)
                        result[column.variable.name] = self.table.encode(col)
                print(results)
                results.append(result)
            result = Table(results, encoded=True,
                           index=index).copy_metadata(self.table)
            return result
