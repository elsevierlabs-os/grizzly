from .types import URI, LangStr, TypedStr, Bnode
import numpy as np

cdef Stream* advance(Stream* stream, char* exception=NULL) except <Stream*>(-1):
    stream.i += 1
    if stream.i >= stream.length:
        if exception:
            return <Stream*>(-1)# raise Exception((<bytes>exception)%stream.i)
    else:
        stream.c = stream.string[stream.i]
    return stream
#
# def eat_whitespace(i, string, length, exception=None):
#     i, c = advance(i, string, length, exception)
#     while c in whitespace:
#         i, c = advance(i, string, length, exception)
#     return i, c

rdf_type = URI('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')

cdef char open_uri = ord('<')
cdef char close_uri = ord('>')
cdef char dot = ord('.')
cdef char semicolon = ord(';')
cdef char comma = ord(',')
cdef char colon = ord(':')
cdef char singlequote = ord("'")
cdef char doublequote = ord('"')
cdef char backslash = ord('\\')
cdef char atsign = ord('@')
cdef char carret = ord('^')
cdef char hash = ord('#')
cdef char underscore = ord('_')
cdef char a = ord('a')
# cdef char* whitespace = b' \n\t'
# cdef char* punctuation = b',;.'
cdef char* escapable = b'tbnrf"\'\\'


cdef class Triples:

    cdef list triples
    cdef list vertices
    cdef dict codes
    cdef dict prefixes
    cdef str baseIRI

    cdef object subject
    cdef object predicate
    cdef object object

    cdef object datatype
    cdef str extra

cdef int encode(object string, Triples triples):
    size = len(triples.vertices)
    code = triples.codes.get(string, size)
    if code == size:
        triples.codes[string] = size
        triples.vertices.append(string)
    return code

cdef struct Stream:

    int i
    char* string
    int length
    char c

def parse(char* string):
    cdef Stream s = Stream(i=0, string=string, length=len(string), c=string[0])
    cdef Stream* stream = &s
    cdef Triples triples = _parse(stream)
    return (triples.triples, triples.vertices,
            triples.codes, triples.prefixes, triples.baseIRI)

cdef Triples _parse(Stream* stream):

    cdef int start = 0
    cdef int escape = 0
    cdef Triples triples = Triples()
    triples.triples = []
    triples.vertices = [np.nan]
    triples.codes = {np.nan: 0}
    triples.prefixes = {}
    value = None
#     cdef char* subject = NULL
#     cdef char* predicate = NULL
#     cdef char* object = NULL
#     cdef char* value = NULL

    while stream.i < stream.length:
        if stream.c == open_uri:
            triples = parse_uri(stream, triples)
        elif stream.c == doublequote or stream.c == singlequote:
            triples = parse_literal(stream, triples)
        elif stream.c == dot:
            triples = parse_dot(stream, triples)
        elif stream.c == semicolon:
            triples = parse_semicolon(stream, triples)
        elif stream.c == comma:
            triples = parse_comma(stream, triples)
        elif stream.c == atsign:
            if stream.i+6 < stream.length and stream.string[stream.i+1:stream.i+7] == b'prefix':
                triples = parse_prefix_declaration(stream, triples)
            elif stream.i+4 < stream.length and stream.string[stream.i+1:stream.i+4] == b'base':
                stream.i += 4
                stream = advance(stream, 'Expected base definition at %s.')

        elif stream.c == underscore:
            pass
        elif stream.c == a:
            triples = parse_a(stream, triples)
        elif stream.c == hash:
            triples = parse_comment(stream, triples)
        elif stream.c not in b' \n\t': #whitespace
            triples = parse_prefixed_uri(stream, triples)

        stream = advance(stream)

    return triples

cdef parse_comment(Stream* stream, Triples triples):
    while stream.c != b'\n':
        stream = advance(stream, '1 Expected prefix definition at %s.')
    return triples

cdef parse_prefix_declaration(Stream* stream, Triples triples):
    stream.i += 6
    stream = advance(stream, '1 Expected prefix definition at %s.')
    while stream.c in b' \n\t':
        stream = advance(stream, '2 Expected prefix definition at %s.')
    triples = parse_prefixed_uri(stream, triples, declaration=True)
    prefix = triples.extra
    stream = advance(stream, '3 Expected prefix definition at %s.')
    while stream.c in b' \n\t':
        stream = advance(stream, '4 Expected prefix definition at %s.')
    if stream.c == open_uri:
        triples = parse_uri(stream, triples, declaration=True)
        expanded_prefix = triples.extra
    else:
        raise Exception()
    stream = advance(stream, '6 Expected prefix definition at %s.')
    while stream.c in b' \n\t':
        stream = advance(stream, '7 Expected prefix definition at %s.')
    if stream.c != dot:
        raise Exception()
    triples.prefixes[prefix] = expanded_prefix
    return triples

cdef parse_a(Stream* stream, Triples triples):
    value = encode(rdf_type, triples)
    if triples.subject is None:
        triples.subject = value
    elif triples.predicate is None:
        triples.predicate = value
    elif triples.object is None:
        triples.object = value
    return triples

cdef parse_prefixed_uri(Stream* stream, Triples triples, declaration=False, datatype=False):
    cdef int start = stream.i
    while stream.c != colon:
        stream = advance(stream, 'Prefix not finished at %s.')
        if stream.c in b' \n\t':
            raise Exception('Expected prefix at %i'%stream.i)
    prefix = stream.string[start:stream.i].decode(encoding='utf-8')
    if declaration:
        triples.extra = prefix
        return triples
    expanded_prefix = triples.prefixes.get(prefix, False)
    if not expanded_prefix:
        raise Exception('unknown prefix %s at %s'%(prefix, stream.i))
    stream = advance(stream, 'Literal not finished at %s.')
    start = stream.i
    while stream.c not in b' \n\t':
        stream = advance(stream, 'Prefix not finished at %s.')
    suffix = stream.string[start:stream.i].decode(encoding='utf-8')

    if datatype:
        triples.datatype = URI(expanded_prefix+suffix)
    else:
        value = encode(URI(expanded_prefix+suffix), triples)
    if triples.subject is None:
        triples.subject = value
    elif triples.predicate is None:
        triples.predicate = value
    elif triples.object is None:
        triples.object = value
    return triples


cdef parse_uri(Stream* stream, Triples triples, declaration=False, datatype=False):
    cdef int start = stream.i + 1
    while stream.c != close_uri:
        stream = advance(stream, 'URI not finished at %s.')
        if stream.c == open_uri:
            raise Exception('URI error at %i'%stream.i)
    if declaration:
        triples.extra = stream.string[start:stream.i].decode(encoding='utf-8')
        return triples
    if datatype:
        triples.datatype = URI(stream.string[start:stream.i].decode(encoding='utf-8'))
    else:
        value = encode(URI(stream.string[start:stream.i].decode(encoding='utf-8')), triples)
    if triples.subject is None:
        triples.subject = value
    elif triples.predicate is None:
        triples.predicate = value
    elif triples.object is None:
        triples.object = value
    return triples

cdef parse_literal(Stream* stream, Triples triples):
    quotetype = stream.c
    cdef int start = stream.i + 1
    stream = advance(stream, 'Literal not finished at %s.')
    while stream.c != quotetype:
        if stream.c == backslash:
            stream = advance(stream, 'Escape not finished at %s.')
            if not stream.c in b'tbnrf"\'\\': #escapable
                raise Exception('Cannot escape %s at %s.'%(stream.c, stream.i))
        stream = advance(stream, 'Literal not finished at %s.')
    value = stream.string[start:stream.i].decode(encoding='utf-8')
    if not triples.subject and triples.predicate:
        print(triples.subject, triples.predicate, triples.object)
        raise Exception('literal not in object positionat %s.'%stream.i)
    stream = advance(stream)
    if stream.c == atsign:
        triples = parse_langtag(stream, triples)
        value = encode(LangStr(value).set_lang(triples.datatype), triples)
    elif stream.c == carret:
        triples = parse_datatype(stream, triples)
        value = encode(TypedStr(value).set_datatype(triples.datatype), triples)
    else:
        value = encode(TypedStr(value), triples)
    triples.object = value
    return triples

cdef parse_langtag(Stream* stream, Triples triples):
    stream = advance(stream, 'Language tag expected at %s.')
    if stream.c in b' \n\t,;.': #whitespace or punctuation
        raise Exception('Language tag expected at %s.'%stream.i)
    start = stream.i
    while not (stream.c in b' \n\t,;.'):
        stream = advance(stream, 'Language tag expected at %s.')
    triples.datatype = stream.string[start:stream.i].decode(encoding='utf-8')
    return triples

cdef parse_datatype(Stream* stream, Triples triples):
    stream = advance(stream, 'Language tag expected at %s.')
    if stream.c == carret:
        stream = advance(stream, 'Language tag expected at %s.')
        if stream.c == open_uri:
            triples = parse_uri(stream, triples, declaration=False, datatype=True)
        else:
            triples = parse_prefixed_uri(stream, triples, declaration=False, datatype=True)
    else:
        raise Exception('Datatype expected at %s.'%stream.i)
    return triples

cdef parse_dot(Stream* stream, Triples triples):
    if triples.subject and triples.predicate and triples.object:
        triples.triples.append((triples.subject, triples.predicate, triples.object))
        triples.subject = None
        triples.predicate = None
        triples.object = None
    else:
        print((triples.subject, triples.predicate, triples.object))
        raise Exception('Dot error at %i'%stream.i)
    return triples

cdef parse_semicolon(Stream* stream, Triples triples):
    if triples.subject and triples.predicate and triples.object:
        triples.triples.append((triples.subject, triples.predicate, triples.object))
        triples.predicate = None
        triples.object = None
    else:
        print((triples.subject, triples.predicate, triples.object))
        raise Exception('Semicolon error at %i'%stream.i)
    return triples

cdef parse_comma(Stream* stream, Triples triples):
    if triples.subject and triples.predicate and triples.object:
        triples.triples.append((triples.subject, triples.predicate, triples.object))
        triples.object = None
    else:
        print((triples.subject, triples.predicate, triples.object))
        raise Exception('Comma error at %i'%stream.i)
    return triples
