from grizzly.types import LangStr, TypedStr
import grizzly as gz

def parse(str string):

    # t0 = time.time()

    whitespace = {' ', '\n', '\t'}

    triples = []

    subject = None
    predicate = None
    object = None

    start = 0
    uri = False
    literal = False
    lang = False

    cdef int i
    cdef Py_UCS4 c

    for i, c in enumerate(string):
        if uri and c != u'>':
            continue
        elif literal and c != u'"':
            continue
        elif c == u'<' and not literal:
            start = i + 1
            uri = True
        elif c == u'>' and uri:
            value = string[start:i]
            start = 0
            uri = False
            if subject is None:
                subject = value
            elif predicate is None:
                predicate = value
            else:
                triples.append((subject, predicate, value))
                subject = None
                predicate = None
        elif c == u'"' and not literal:
            start = i + 1
            literal = True
        elif c == u'"' and literal:
            object = string[start:i]
            start = 0
            literal = False
            # if not (subject and predicate):
            #     raise Exception
        elif c == u'@' and object:
            start = i + 1
            lang = True
        # elif c =='^' and object:

        elif c in whitespace and lang:
            value = string[start:i]
            start = 0
            lang = False
            triples.append((subject, predicate, LangStr(object).set_lang(value)))
            subject = None
            predicate = None
            object = None
        elif c in whitespace and object:
            triples.append((subject, predicate, TypedStr(object)))
            subject = None
            predicate = None
            object = None

    # print(time.time() - t0)
    return triples


def load_triples_grizzly_cython(filename):

    with open(filename) as f:
        string = f.read()
    triples = parse(string)
    return gz.Graph(triples)
