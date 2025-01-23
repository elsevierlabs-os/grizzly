cdef (int, char) advance(int i, char* string, int length, exception=None):
    i += 1
    if i >= length:
        if exception:
            raise Exception(exception%i)
        else:
            return i, 0
    cdef char c = string[i]
    return i, c


cdef char open_uri = ord('<')
cdef char close_uri = ord('>')
cdef char dot = ord('.')
cdef char semicolon = ord(';')
cdef char comma = ord(',')
cdef char singlequote = ord("'")
cdef char doublequote = ord('"')
cdef char backslash = ord('\\')
cdef char at = ord('@')

def parse(char* string):

    cdef int length = len(string)
    cdef int i = 0
    cdef int start = 0
    cdef int escape = 0
    subject = None
    predicate = None
    object = None

    triples = []
    cdef char c = string[0]

    while i < length:
        if c == open_uri:
            start = i + 1
            while c != close_uri:
                i, c = advance(i, string, length, 'URI not finished at %s.')
                if c == open_uri:
                    raise Exception('URI error at %i'%i)
            value = string[start:i]
            if subject is None:
                subject = value
            elif predicate is None:
                predicate = value
            elif object is None:
                object = value
        elif c == doublequote or c == singlequote:
            quotetype = c
            i += 1
            start = i
            if i >= length:
                break
            c = string[i]
            while c != quotetype or escape == i - 1:
                if c == backslash and escape != i - 1:
                    escape = i
                i, c = advance(i, string, length, 'Literal not finished at %s.')
            value = string[start:i]
            if subject and predicate:
                object = value
            else:
                raise Exception('literal not in object position.')
            i += 1
            start = i
            if i >= length:
                break
            c = string[i]
            if c == at:
                pass
        elif c == dot:
            if subject and predicate and object:
                triples.append((subject, predicate, object))
                subject = None
                predicate = None
                object = None
            else:
                print((subject, predicate, object))
                raise Exception('Dot error at %i'%i)
        elif c == semicolon:
            if subject and predicate and object:
                triples.append((subject, predicate, object))
                predicate = None
                object = None
            else:
                print((subject, predicate, object))
                raise Exception('Semicolon error at %i'%i)(i)
        elif c == comma:
            if subject and predicate and object:
                triples.append((subject, predicate, object))
                object = None
            else:
                print((subject, predicate, object))
                raise Exception('Comma error at %i'%i)

        i, c = advance(i, string, length)

    return triples
