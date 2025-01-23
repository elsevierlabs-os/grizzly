def advance(i, string, length, exception=None):
    i += 1
    if i >= length:
        if exception:
            raise Exception(exception%i)
        else:
            return i, 0
    c = string[i]
    return i, c


open_uri = ord('<')
close_uri = ord('>')
dot = ord('.')
semicolon = ord(';')
comma = ord(',')
singlequote = ord("'")
doublequote = ord('"')
backslash = ord('\\')
at = ord('@')

def parse(string):

    length = len(string)
    i = 0
    start = 0
    escape = 0
    subject = None
    predicate = None
    object = None

    triples = []
    c = string[0]

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
