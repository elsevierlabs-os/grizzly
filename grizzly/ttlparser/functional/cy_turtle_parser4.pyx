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

cdef char open_uri = ord('<')
cdef char close_uri = ord('>')
cdef char dot = ord('.')
cdef char semicolon = ord(';')
cdef char comma = ord(',')
cdef char singlequote = ord("'")
cdef char doublequote = ord('"')
cdef char backslash = ord('\\')
cdef char atsign = ord('@')
cdef char carret = ord('^')
cdef char underscore = ord('_')
# cdef char* whitespace = b' \n\t'
# cdef char* punctuation = b',;.'
cdef char* escapable = b'tbnrf"\'\\'


class Triples:

    triples = []
    subject = None
    predicate = None
    object = None


cdef struct Stream:

    int i
    char* string
    int length
    char c

def parse(char* string):
  cdef Stream s = Stream(i=0, string=string, length=len(string), c=string[0])
  cdef Stream* stream = &s
  return _parse(stream)

cdef _parse(Stream* stream):

    cdef int start = 0
    cdef int escape = 0
    cdef list triples = []
    subject = None
    predicate = None
    object = None
    value = None
#     cdef char* subject = NULL
#     cdef char* predicate = NULL
#     cdef char* object = NULL
#     cdef char* value = NULL

    while stream.i < stream.length:
        if stream.c == open_uri:
            start = stream.i + 1
            while stream.c != close_uri:
                stream = advance(stream, 'URI not finished at %s.')
                if stream.c == open_uri:
                    raise Exception('URI error at %i'%stream.i)
            value = stream.string[start:stream.i]
            if subject is None:
                subject = value
            elif predicate is None:
                predicate = value
            elif object is None:
                object = value
        elif stream.c == doublequote or stream.c == singlequote:
            quotetype = stream.c
            start = stream.i + 1
            stream = advance(stream, 'Literal not finished at %s.')
            while stream.c != quotetype:
                if stream.c == backslash:
                    stream = advance(stream, 'Escape not finished at %s.')
                    if not stream.c in b'tbnrf"\'\\': #escapable
                        raise Exception('Cannot escape %s at %s.'%(stream.c, stream.i))
                stream = advance(stream, 'Literal not finished at %s.')
            value = stream.string[start:stream.i]
            if subject and predicate:
                object = value
            else:
                print(subject, predicate, object)
                raise Exception('literal not in object positionat %s.'%stream.i)
            stream = advance(stream)
            if stream.c == atsign:
                stream = advance(stream, 'Language tag expected at %s.')
                if stream.c in b' \n\t,;.': #whitespace or punctuation
                    raise Exception('Language tag expected at %s.'%stream.i)
                start = stream.i
                while not (stream.c in b' \n\t,;.'):
                    stream = advance(stream, 'Language tag expected at %s.')
                language = stream.string[start:stream.i]
            elif stream.c == carret:
                stream = advance(stream, 'Language tag expected at %s.')
                if stream.c == carret:
                    stream = advance(stream, 'Language tag expected at %s.')
                    start = stream.i
                else:
                    raise Exception('Datatype expected at %s.'%stream.i)
                datatype = stream.string[start:stream.i]
        elif stream.c == dot:
            if subject and predicate and object:
                triples.append((subject, predicate, object))
                subject = None
                predicate = None
                object = None
            else:
                print((subject, predicate, object))
                raise Exception('Dot error at %i'%stream.i)
        elif stream.c == semicolon:
            if subject and predicate and object:
                triples.append((subject, predicate, object))
                predicate = None
                object = None
            else:
                print((subject, predicate, object))
                raise Exception('Semicolon error at %i'%stream.i)
        elif stream.c == comma:
            if subject and predicate and object:
                triples.append((subject, predicate, object))
                object = None
            else:
                print((subject, predicate, object))
                raise Exception('Comma error at %i'%stream.i)
        elif stream.c == atsign:
            if stream.i+6 < stream.length and stream.string[stream.i+1:stream.i+7] == b'prefix':
                stream.i += 6
                stream = advance(stream, 'Expected prefix definition at %s.')
                # while not c ==
            elif stream.i+4 < stream.length and stream.string[stream.i+1:stream.i+5] == b'base':
                stream.i += 4
                stream = advance(stream, 'Expected base definition at %s.')

        elif stream.c == underscore:
            pass
        elif stream.c not in b' \n\t': #whitespace
            stream = advance(stream, 'Unexpected character at %s.')

        stream = advance(stream)

    return triples
