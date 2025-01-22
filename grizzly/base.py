import operator
import pandas as pd
from pandas.core.internals import BlockManager
import numpy as np
from functools import reduce, partial
from . import model
from .parser import SPARQLParser, GFDSLParser
from .prefix import common_prefixes, replace_prefix
from .types import URI, LangStr, TypedStr, type_string

def Table(*args, **kwargs):
    from .table import Table
    return Table(*args, **kwargs)

# def Graph(*args, **kwargs):
#     from .graph import Graph
#     return Graph(*args, **kwargs)

def directly_queryable(rule_name):
    def intermediate(function):
        def wrapped_function(self, query, *args, ast=False, **kwargs):
            if not ast:
                query = self.parse(query, rule_name=rule_name)
            return function(self, query, *args, **kwargs)
        return wrapped_function
    return intermediate


class Base(pd.DataFrame):

    _metadata = ['vertices', 'codes', 'prefixes', 'baseIRI', 'parsers', 'encoded']

    def __init__(self, data, *args, vertices=[], codes={}, prefixes={},
                 baseIRI='', encoded=False, add_common_prefixes=True, **kwargs):
        if add_common_prefixes:
            custom_prefixes = prefixes
            prefixes = common_prefixes.copy()
            prefixes.update(custom_prefixes)
        already_encoded = getattr(data, 'encoded', False)
        if not (already_encoded or encoded) and type(data) is not BlockManager:
            data, vertices, codes = self.__class__._initial_encode(data, prefixes)
        super().__init__(data, *args, **kwargs)
        if getattr(data, 'encoded', False):
            self.copy_metadata(data)
        else:
            self.vertices = vertices.copy()
            self.codes = codes.copy()
            self.prefixes = prefixes.copy()
            self.baseIRI = baseIRI
            self.parsers = {'SPARQL': partial(SPARQLParser().parse,
                                    semantics=model.GraphModelBuilderSemantics()),
                            'GFDSL': partial(GFDSLParser().parse,
                                    semantics=model.GraphModelBuilderSemantics())}
            self.encoded = True

    @classmethod
    def from_df(cls, df, custom_prefixes={}, baseIRI=''):
        return cls(df, prefixes=custom_prefixes, baseIRI=baseIRI)

    @classmethod
    def _initial_encode(cls, data, prefixes={}):
        df = pd.DataFrame(data).applymap(lambda x: type_string(replace_prefix(x, prefixes)))
        vertices = [np.nan] + list(set(df.values.ravel('K')) - set([np.nan]))
        codes = dict((name, i) for i, name in enumerate(vertices))
        encoded = pd.DataFrame(df).applymap(lambda x: 0 if pd.isna(x) else codes[x]).astype(np.int32)
        return encoded, vertices, codes

    @property
    def _constructor(self):
        def constructor(*args, **kwargs):
            data = pd.DataFrame(*args, **kwargs)
            if len(data.columns) == 3:
                return self.__class__(data, encoded=True).copy_metadata(self)
            else:
                return Table(data, encoded=True).copy_metadata(self)
        return constructor

    @property
    def _constructor_sliced(self):
        def constructor(*args, **kwargs):
            return Series(*args, vertices=self.vertices, codes=self.codes,
                          prefixes=self.prefixes, baseIRI=self.baseIRI,
                          parsers=self.parsers, **kwargs)
        return constructor

    def parse(self, query, rule_name='query', parser='SPARQL'):
        '''Parses a string `query` with the parser indicated in `parser`. By
        default assumes to start with the start rule `query` but other rules can
        be as argument to `rule_name`.
        '''
        return self.parsers[parser](query, rule_name=rule_name)

    @directly_queryable(rule_name='term')
    def term(self, query, encode=False):
        '''Resolves any valid RDF term (variable, IRI, prefixed IRI, literal, ...)
        and returns a typed object. E.g. `table.term('?variable')` returns a
        the corresponding data column as Series; `graph.term('"xyz"@en')` gives
        a `LangStr` object with value `xyz`; `graph.term('skos:prefLabel')`
        returns a `URI` object with the value
        `'http://www.w3.org/2004/02/skos/core#prefLabel'`.
        '''
        term = query.ast if type(query) is model.Term else query
        if type(term) is model.Variable:
            return self.variable(term, ast=True)
        elif type(term) is model.Resource:
            value = self.resource(term.value, ast=True)
        elif type(term) is model.Literal:
            value = self.literal(term.value, ast=True)
        if encode:
            value = self.encode(value)
        return value

    @directly_queryable(rule_name='variable')
    def variable(self, query):
        value = self[query.name].copy()
        return value

    @directly_queryable(rule_name='resource')
    def resource(self, query):
        if type(query) is model.Full_iri:
            value = URI(query.value)
        elif type(query) is model.Relative_iri:
            value = URI(self.baseIRI + query.value)
        elif type(query) is model.Prefixed:
            value = URI(self.prefixes[query.prefix] + query.postfix)
        elif type(query) is model.Rdf_type:
            value = URI('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
        return value

    @directly_queryable(rule_name='literal')
    def literal(self, query):
        if type(query) is model.Boolean_literal:
            value = True if type(query.value) is model.TRUE else False
        elif type(query) is model.Numeric_literal:
            numeric_literal = query.value
            if type(numeric_literal) is model.Integer:
                value = int(numeric_literal.value)
            elif type(numeric_literal) is model.Decimal:
                value = float(numeric_literal.value)
            elif type(numeric_literal) is model.Double:
                base = numeric_literal.base.value
                sign = numeric_literal.sign or ''
                exponent = numeric_literal.exponent.value
                value = float(base + 'e' + sign + exponent)
        elif type(query) is model.Rdf_literal:
            if query.language_tag:
                value = LangStr(query.value).set_lang(query.language_tag)
            elif query.datatype:
                datatype = str(self.resource(query.datatype.value, ast=True))
                value = TypedStr(query.value).set_datatype(datatype)
            else:
                value = TypedStr(query.value)
        return value

    @directly_queryable(rule_name='expression')
    def expression(self, expr):
        return reduce(operator.__or__,
                [self._and_expression(sub_expr) for sub_expr in expr])

    def _and_expression(self, expr):
        return reduce(operator.__and__,
                [self._comparison(sub_expr) for sub_expr in expr])

    def _comparison(self, expr):
        left = self._artihmetic_expression(expr.left)
        if expr.right is not None:
            if type(expr.op) in [model.In, model.Notin]:
                right = [self.expression(item, ast=True) for item in expr.right]
                op = type(expr.op)
            else:
                right = self._artihmetic_expression(expr.right)
                op = expr.op
            return operators[op](left, right)
        else:
            return left

    def _artihmetic_expression(self, expr):
        left = self._mult_expression(expr.left)
        if expr.right is not None:
            right = self._artihmetic_expression(expr.right)
            return operators[expr.op](left, right)
        else:
            return left

    def _mult_expression(self, expr):
        left = self._unary_expression(expr.left)
        if expr.right is not None:
            right = self._mult_expression(expr.right)
            return operators[expr.op](left, right)
        else:
            return left

    def _unary_expression(self, expr):
        expression = self._primary_expression(expr.expression)
        return unary_operators[expr.op](expression)

    def _primary_expression(self, expr):
        if type(expr) is model.Call:
            return self.call(expr.ast, ast=True)
        elif type(expr) is model.Term:
            return self.term(expr.ast, ast=True)
        else:
            return self.expression(expr)

    @directly_queryable(rule_name='call')
    def call(self, expr):
        if type(expr) is model.One_arg_call:
            argument = self.expression(expr.argument, ast=True)
            return functions[expr.name.upper()](argument)
        elif type(expr) is model.Two_arg_call:
            argument1 = self.expression(expr.argument1, ast=True)
            argument2 = self.expression(expr.argument2, ast=True)
            return functions[expr.name.upper()](argument1, argument2)
        elif type(expr) is model.Aggregate_call:
            argument = self.expression(expr.argument, ast=True)
            if expr.distinct:
                argument = argument.drop_duplicates()
            return functions[expr.name.upper()](argument)
        elif type(expr) is model.If:
            condition = self.expression(expr.condition, ast=True)
            succeed = condition.copy()
            succeed[:] = self.expression(expr.succeed, ast=True)
            fail = self.expression(expr.fail, ast=True)
            return succeed.where(condition, fail)
        elif type(expr) is model.Bound:
            return self[expr.variable.name].notna()
        else:
            raise NotImplementedError('The function "%s" has not been implemented yet.'%expr.name)

    def constrain(self, constraints, parts):
        parts = [part for part in parts if part in constraints]
        if isinstance(constraints, pd.DataFrame):
            result = self.merge(constraints[parts].drop_duplicates())
        else:
            result = self
            for part in parts:
                result = result[result[part] == constraints[part]]
        return result

    def filter(self, expression):
        '''Filter values according to expression following the GraphFrames
        pattern.
        '''
        parsed = self.parse(expression, rule_name='expression', parser='GFDSL')
        mask = self.decode().expression(parsed, ast=True)
        return self[mask]

    def copy_metadata(self, source):
        for field in self._metadata:
            source_field = getattr(source, field)
            setattr(self, field, source_field)
        return self

    def decode(self, value=None):
        if value is None:
            if not self.encoded:
                return self
            result = (self.fillna(0)
                          .astype(int)
                          .applymap(lambda x: self.vertices[x])
                     )
            result.encoded = False
            return result
        else:
            return self.vertices[value]

    def encode(self, value=None):
        if isinstance(value, pd.Series):
            return value.apply(self.encode_value)
        elif isinstance(value, pd.DataFrame):
            return value.applymap(self.encode_value)
        elif value is None:
            return self.applymap(self.encode_value)
        else:
            return self.encode_value(value)

    def encode_value(self, value):
        code = self.codes.get(value, None)
        if code is None:
            code = len(self.codes)
            self.codes[value] = code
            self.vertices.append(value)
        return code

    def to_pandas(self):
        decoded = self.decode().applymap(
                        lambda x: str(x) if isinstance(x,str) else x)
        return pd.DataFrame(decoded)

    def to_koalas(self):
        import koalas as kl
        decoded = self.decode().applymap(
                        lambda x: str(x) if isinstance(x,str) else x)
        return kl.WordFrame(decoded)

    def to_csv(self, *args, index=False, decode=True, **kwargs):
        if decode:
            decoded = self.decode().to_csv(*args, index=index, decode=False, **kwargs)
        else:
            super().to_csv(*args, index=index, **kwargs)


class Series(pd.Series):

    _metadata = ['vertices', 'codes', 'prefixes', 'baseIRI', 'parsers']

    def __init__(self, *args, vertices=[], codes={}, prefixes={}, baseIRI='', parsers=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.vertices = vertices.copy()
        self.codes = codes.copy()
        self.prefixes = prefixes.copy()
        self.baseIRI = baseIRI
        self.parsers = {'SPARQL': partial(SPARQLParser().parse,
                                semantics=model.GraphModelBuilderSemantics()),
                        'GFDSL': partial(GFDSLParser().parse,
                                semantics=model.GraphModelBuilderSemantics())}
    @property
    def _constructor(self):
        return Series

    @property
    def _constructor_expanddim(self):
        def constructor(*args, **kwargs):
            return Table(*args, encoded=True, **kwargs).copy_metadata(self)
        return constructor



operators = {
'=': operator.__eq__,
'!=': operator.__ne__,
'<': operator.__lt__,
'>': operator.__gt__,
'<=': operator.__le__,
'>=': operator.__ge__,
'+': operator.__add__,
'-': operator.__sub__,
'*': operator.__mul__,
'/': operator.__truediv__,
model.In: lambda x, y: x.isin(y),
model.Notin: lambda x, y: ~x.isin(y)
}

unary_operators = {
None: lambda x: x,
'-': operator.__neg__,
'+': operator.__pos__,
'!': operator.__inv__
}

functions = {
'STR': lambda x: x.astype(str),
'LANG': lambda x: x.apply(lambda y: getattr(y, 'lang', np.nan)),
'DATATYPE': lambda x: x.apply(lambda y: getattr(y, 'datatype', np.nan)),
#|IRI|URI|
'ABS': lambda x: x.abs(),
'UCASE': lambda x: x.str.upper(),
# CEIL|FLOOR|ROUND|STRLEN|UCASE|LCASE|ENCODE_FOR_URI|YEAR|MONTH|DAY|HOURS|MINUTES|SECONDS|TIMEZONE|TZ|MD5|SHA1|SHA256|SHA384|SHA512|isIRI|isURI|isBLANK|isLITERAL|isNUMERIC
'STRLEN': lambda x: x.str.len(),
#LANGMATCHES|
'CONTAINS': lambda x, y: x.str.contains(y),
'STRSTARTS': lambda x, y: x.str.startswith(y),
'STRENDS': lambda x, y: x.str.endswith(y),
#|STRBEFORE|STRAFTER|STRLANG|STRDT|sameTerm"
'COUNT': len,
'SUM': lambda x: x.sum(),
'MIN': lambda x: x.min(),
'MAX': lambda x: x.max(),
'AVG': lambda x: x.mean(),
'SAMPLE': lambda x: x.head(1),
}
