#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.

from __future__ import print_function, division, absolute_import, unicode_literals

from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics


class ModelBase(Node):
    pass


class GraphModelBuilderSemantics(ModelBuilderSemantics):
    def __init__(self, context=None, types=None):
        types = [
            t for t in globals().values()
            if type(t) is type and issubclass(t, ModelBase)
        ] + (types or [])
        super(GraphModelBuilderSemantics, self).__init__(context=context, types=types)


class BaseDeclaration(ModelBase):
    iri = None


class PrefixDeclaration(ModelBase):
    iri = None
    prefix = None


class SelectQuery(ModelBase):
    dataset_clause = None
    select_clause = None
    solution_modifier = None
    where_clause = None


class ConstructQuery(ModelBase):
    construct_clause = None
    dataset_clause = None
    where_clause = None


class UpdateQuery(ModelBase):
    pass


class Group(ModelBase):
    pass


class Triple(ModelBase):
    obj = None
    pre = None
    sub = None


class Optional(ModelBase):
    pass


class Minus(ModelBase):
    pass


class Union(ModelBase):
    left = None
    right = None


class Filter(ModelBase):
    pass


class ExistsGroup(ModelBase):
    group = None
    predicate = None


class Bind(ModelBase):
    pass


class Data_block(ModelBase):
    pass


class Call(ModelBase):
    pass


class One_arg_call(ModelBase):
    argument = None
    name = None


class Two_arg_call(ModelBase):
    argument1 = None
    argument2 = None
    name = None


class Aggregate_call(ModelBase):
    argument = None
    distinct = None
    name = None


class If(ModelBase):
    condition = None
    fail = None
    succeed = None


class Bound(ModelBase):
    variable = None


class Term(ModelBase):
    pass


class Variable(ModelBase):
    name = None


class Resource(ModelBase):
    value = None


class Full_iri(ModelBase):
    value = None


class Relative_iri(ModelBase):
    value = None


class Prefixed(ModelBase):
    postfix = None
    prefix = None


class Rdf_type(ModelBase):
    pass


class Literal(ModelBase):
    value = None


class Boolean_literal(ModelBase):
    value = None


class Numeric_literal(ModelBase):
    value = None


class Rdf_literal(ModelBase):
    datatype = None
    language_tag = None
    value = None


class Integer(ModelBase):
    value = None


class Decimal(ModelBase):
    value = None


class Double(ModelBase):
    base = None
    exponent = None
    sign = None


class TRUE(ModelBase):
    pass


class FALSE(ModelBase):
    pass


class All(ModelBase):
    pass


class Exists(ModelBase):
    pass


class NotExists(ModelBase):
    pass


class Asc(ModelBase):
    pass


class Desc(ModelBase):
    pass


class Undef(ModelBase):
    pass


class Distinct(ModelBase):
    pass


class Reduced(ModelBase):
    pass


class In(ModelBase):
    pass


class Notin(ModelBase):
    pass
