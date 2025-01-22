import pandas as pd


class URI(str):

    def __getattribute__(self, key):
        if key in ['lang', 'set_lang', '__hash__', '__html__']:
            return super().__getattribute__(key)
        def wrapped(*args, **kwargs):
            result = getattr(str(self), key)(*args, **kwargs)
            if isinstance(result, str):
                return URI(result)
            else:
                return result
        return wrapped

    def __hash__(self):
        return hash((str(self), 'URI'))

    def __html__(self):
        return self

class LangStr(str):

    lang = 'en'
    datatype = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#langString'

    def __getattribute__(self, key):
        if key in ['lang', 'set_lang', 'datatype', '__hash__', '__html__']:
            return super().__getattribute__(key)
        def wrapped(*args, **kwargs):
            result = getattr(str(self), key)(*args, **kwargs)
            if isinstance(result, str):
                return LangStr(result).set_lang(self.lang)
            else:
                return result
        return wrapped

    def set_lang(self, lang):
        string = LangStr(self)
        string.lang = lang
        return string

    def __hash__(self):
        return hash((str(self), self.lang))

    def __html__(self):
        return self

class TypedStr(str):

    datatype = 'http://www.w3.org/2001/XMLSchema#string'

    def __getattribute__(self, key):
        if key in ['datatype', 'set_datatype', '__hash__', '__html__']:
            return super().__getattribute__(key)
        elif key in ['lang']:
            raise AttributeError()
        def wrapped(*args, **kwargs):
            result = getattr(str(self), key)(*args, **kwargs)
            if isinstance(result, str):
                return TypedStr(result).set_datatype(self.datatype)
            else:
                return result
        return wrapped

    def set_datatype(self, datatype):
        string = TypedStr(self)
        string.datatype = datatype
        return string

    def __hash__(self):
        return hash((str(self), self.datatype))

    def __html__(self):
        return self

class Bnode(str):

    def __getattribute__(self, key):
        if key in ['__hash__', '__html__']:
            return super().__getattribute__(key)
        elif key in ['lang']:
            raise AttributeError()
        def wrapped(*args, **kwargs):
            result = getattr(str(self), key)(*args, **kwargs)
            if isinstance(result, str):
                return TypedStr(result).set_datatype(self.datatype)
            else:
                return result
        return wrapped

    def __hash__(self):
        return hash((str(self), 'Bnode'))

    def __html__(self):
        return self

def json_to_typed(value):
    if pd.isna(value):
        return value
    elif type(value) is str:
        return URI(value) if value.startswith('http') else TypedStr(value)
    elif value['type'] == 'uri':
        return URI(value['value'])
    elif value['type'] == 'bnode':
        return Bnode(value['value'])
    elif value['type'] == 'literal':
        if 'xml:lang' in value:
            # raise Exception('did not expect xml:lang in %s' % value)
            return LangStr(value['value']).set_lang(value['xml:lang'])
        elif 'lang' in value:
            return LangStr(value['value']).set_lang(value['lang'])
        elif 'datatype' not in value:
            return TypedStr(value['value'])
        elif value['datatype'] == 'http://www.w3.org/2001/XMLSchema#bool':
            return value['value'] == 'true'
        elif value['datatype'] == 'http://www.w3.org/2001/XMLSchema#integer':
            return int(value['value'])
        elif value['datatype'] == 'http://www.w3.org/2001/XMLSchema#decimal':
            return float(value['value'])
        elif value['datatype'] == 'http://www.w3.org/2001/XMLSchema#double':
            return float(value['value'])
        elif value['datatype'] == 'http://www.w3.org/2001/XMLSchema#string':
            return TypedStr(value['value'])
        else:
            return TypedStr(value['value']).set_datatype(value['datatype'])

def typed_to_json(value):
    if type(value) is URI:
        return {'value': value, 'type': 'uri'}
    elif type(value) is Bnode:
        return {'value': value, 'type': 'bnode'}
    elif type(value) is LangStr:
        return {'value': value, 'type': 'literal', 'lang': value.lang}
    elif type(value) is TypedStr:
        return {'value': value, 'type': 'literal', 'datatype': value.datatype}
    else:
        return value

def type_string(value):
    if pd.isna(value):
        return value
    elif type(value) is str:
        if value.startswith('http'):
            return URI(value)
        else:
            return TypedStr(value)
    else:
        return value
