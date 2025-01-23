from libc.stdlib cimport malloc, free
from libc.string cimport memcpy

cdef str prints(Node* node, int indent=0):
    cdef int line = 0

    string = '' if node.length == 0 else ''.join([chr(c) for c in node.value[:node.length]])
    if node.id != 0:
        string += '(%s)\n'%node.id
        line = 1
    indent = indent + node.length
    if node.next is not NULL:
        for i in range(256):
            if node.next[i] is not NULL:
                string += ' '*(indent if line > 0 else 0)
                string += prints(node.next[i], indent)
                line += 1
    return string


cdef class Trie:
    cdef Node* root
    cdef int counter

    def __init__(self, strings):
        self.root = make_trie(strings)
        self.counter = 1

    def __dealloc__(self):
        free_trie(self.root)

    def __str__(self):
        return prints(self.root)

#     def __getitem__(self, key):
#         return get_value(self.root, key, len(key))

    def __setitem__(self, key, value):
        add_string(self.root, key, len(key), value)

    cdef int add_string(self, char* string, int length):
        id = add_string(self.root, string, length, self.counter)
        if id == self.counter:
            self.counter += 1
        return id

cdef struct Node:
    int length
    char* value
    int id
    Node** next

cdef Node* new_node(int length=0, char* value=NULL, int id=0, Node** next=NULL):
    cdef Node* node = <Node*>malloc(sizeof(Node))
    node.length = length
    node.value = value
    node.id = id
    node.next = next
    return node

cdef Node** new_array():
    cdef Node** array = <Node**>malloc(sizeof(void*)*256)
    for i in range(256): array[i] = NULL
    return array

cdef Node* make_trie(strings):
    cdef Node* root = new_node()
    cdef int counter = 1

    for string in strings:
        id = add_string(root, string, len(string), counter)
        if id == counter:
            counter += 1
    return root

cdef void free_trie(Node* node):
    if node.next is not NULL:
        for i in range(256):
            if node.next[i] is not NULL:
                free_trie(node.next[i])
        free(node.next)
    if node.value is not NULL:
        free(node.value)
    free(node)

# cdef int get_value(Node* root, char* string, int length):
#     cdef Node* node = root
#     cdef char c

#     for i in range(length):
#         c = string[i]
#         if node.value == 0:
#             if node.next[c] is NULL:
#                 return -1
#             else:
#                 node = node.next[c]
#         elif node.value == c:
#             if node.next is NULL:
#                 return -1
#             else:
#                 node = node.next[0]
#         else:
#             return -1
#     return node.id

cdef char* copy_substring(char* string, int length):
    cdef char* substring = <char*>malloc(sizeof(char)*length)
    cdef int i
    for i in range(length):
        substring[i] = string[i]
    return substring

cdef int common_substring(char* string1, char* string2, int length1, int length2):
    cdef int i = 0
    cdef int end = length1 if length1 < length2 else length2
    while(string1[0] == string2[0] and i < end):
        string1 += 1
        string2 += 1
        i += 1
    return i

cdef int add_string(Node* root, char* string, int length, int id):
    cdef Node* node = root
    cdef char c
    cdef int i = 0
    cdef int sublength
    cdef int common

    while i < length:
        sublength = length - i
        if node.length == 0:
            if node.next is NULL:
                node.value = copy_substring(string+i, sublength)
                node.length = sublength
                break
            else:
                c = string[i]
                if node.next[c] is not NULL:
                    node = node.next[c]
                else:
                    node.next[c] = new_node()
                    node = node.next[c]
        else:
            common = common_substring(node.value, string+i, node.length, sublength)
            if common == node.length:
                if common == sublength:
                    break
                else:
                    if node.next is NULL:
                        node.next = new_array()
                    i = i + common
                    c = string[i]
                    if node.next[c] is not NULL:
                        node = node.next[c]
                    else:
                        node.next[c] = new_node(sublength-common, copy_substring(string+i, sublength))
                        node = node.next[c]
                        break
            else:
                old_length = node.length - common
                old_value = copy_substring(node.value+common, old_length) #node.value + common#

                old_next = node.next
                old_id = node.id
                old_c = old_value[0]
                node.value = copy_substring(node.value, common)
                node.length = common
                node.id = 0
                node.next = new_array()
                node.next[old_c] = new_node(old_length, old_value, old_id, old_next)
                if sublength > common:
                    i = i + common
                    c = string[i]
                    node.next[c] = new_node(sublength-common, copy_substring(string+i, sublength))
                    node = node.next[c]
                break

    if node.id == 0:
        node.id = id
    return node.id


cdef int* new_int_array(int size):
    cdef int* array = <int*>malloc(size * sizeof(int))
    return array

cdef int* resize_array(int* array, int size, int new_size):
    cdef int* new_array = <int*>malloc(new_size * sizeof(int))
    memcpy(new_array, array, size)
    free(array)
    return new_array


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


cdef int ARRAY_SIZE = 10000

cdef struct Triples:

    int* subjects
    int* predicates
    int* objects
    int subject
    int predicate
    int object
    int n
    int limit
    Node* trie
    int counter

cdef Triples* new_triples():
    cdef Triples* triples = <Triples*>malloc(sizeof(Triples))
    triples.subjects = new_int_array(ARRAY_SIZE)
    triples.predicates = new_int_array(ARRAY_SIZE)
    triples.objects = new_int_array(ARRAY_SIZE)
    triples.trie = new_node()
    triples.counter = 1
    triples.n = 0
    triples.limit = ARRAY_SIZE
    return triples

cdef void resize_triples(Triples* triples):
    size = triples.limit
    new_size = triples.limit + ARRAY_SIZE
    triples.subjects = resize_array(triples.subjects, size, new_size)
    triples.predicates = resize_array(triples.predicates, size, new_size)
    triples.objects = resize_array(triples.objects, size, new_size)
    triples.limit = new_size

cdef struct Stream:

    int i
    char* string
    int length
    char c

def parse(char* string):
    cdef Stream s = Stream(i=0, string=string, length=len(string), c=string[0])
    cdef Stream* stream = &s
    return _parse(stream)

cdef int _parse(Stream* stream):

    cdef int start = 0
    cdef int escape = 0
    cdef Triples* triples = new_triples()
    cdef int value = 0
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

    return triples.n


cdef Triples* parse_uri(Stream* stream, Triples* triples):
    cdef int start = stream.i + 1
    while stream.c != close_uri:
        stream = advance(stream, 'URI not finished at %s.')
        if stream.c == open_uri:
            raise Exception('URI error at %i'%stream.i)
    value = add_string(triples.trie, stream.string+start, stream.i-start, triples.counter)#stream.string[start:stream.i]
    if value == triples.counter:
        triples.counter += 1
    if triples.subject == 0:
        triples.subject = value
    elif triples.predicate == 0:
        triples.predicate = value
    elif triples.object == 0:
        triples.object = value
    return triples

cdef Triples* parse_literal(Stream* stream, Triples* triples):
    quotetype = stream.c
    cdef int start = stream.i + 1
    stream = advance(stream, 'Literal not finished at %s.')
    while stream.c != quotetype:
        if stream.c == backslash:
            stream = advance(stream, 'Escape not finished at %s.')
            if not stream.c in b'tbnrf"\'\\': #escapable
                raise Exception('Cannot escape %s at %s.'%(stream.c, stream.i))
        stream = advance(stream, 'Literal not finished at %s.')
    value = add_string(triples.trie, stream.string+start, stream.i-start, triples.counter)#stream.string[start:stream.i]
    if value == triples.counter:
        triples.counter += 1
    if triples.subject and triples.predicate:
        triples.object = value
    else:
        print(triples.subject, triples.predicate, triples.object)
        raise Exception('literal not in object positionat %s.'%stream.i)
    stream = advance(stream)
    if stream.c == atsign:
        triples = parse_langtag(stream, triples)
    elif stream.c == carret:
        triples = parse_datatype(stream, triples)
    return triples

cdef Triples* parse_langtag(Stream* stream, Triples* triples):
    stream = advance(stream, 'Language tag expected at %s.')
    if stream.c in b' \n\t,;.': #whitespace or punctuation
        raise Exception('Language tag expected at %s.'%stream.i)
    start = stream.i
    while not (stream.c in b' \n\t,;.'):
        stream = advance(stream, 'Language tag expected at %s.')
    # cdef int language = triples.trie.add_string(stream.string+start, stream.i-start)#stream.string[start:stream.i]
    return triples

cdef Triples* parse_datatype(Stream* stream, Triples* triples):
    stream = advance(stream, 'Language tag expected at %s.')
    if stream.c == carret:
        stream = advance(stream, 'Language tag expected at %s.')
        start = stream.i
    else:
        raise Exception('Datatype expected at %s.'%stream.i)
    # cdef int datatype = triples.trie.add_string(stream.string+start, stream.i-start)#stream.string[start:stream.i]
    return triples

cdef Triples* parse_dot(Stream* stream, Triples* triples):
    if triples.subject and triples.predicate and triples.object:
        n = triples.n
        if triples.n == triples.limit:
            resize_triples(triples)
        triples.subjects[n] = triples.subject
        triples.predicates[n] = triples.predicate
        triples.objects[n] = triples.object
        triples.subject = 0
        triples.predicate = 0
        triples.object = 0
        triples.n += 1
    else:
        print((triples.subject, triples.predicate, triples.object))
        raise Exception('Dot error at %i'%stream.i)
    return triples

cdef Triples* parse_semicolon(Stream* stream, Triples* triples):
    if triples.subject and triples.predicate and triples.object:
        n = triples.n
        if triples.n == triples.limit:
            resize_triples(triples)
        triples.subjects[n] = triples.subject
        triples.predicates[n] = triples.predicate
        triples.objects[n] = triples.object
        triples.predicate = 0
        triples.object = 0
        triples.n += 1
    else:
        print((triples.subject, triples.predicate, triples.object))
        raise Exception('Semicolon error at %i'%stream.i)
    return triples

cdef Triples* parse_comma(Stream* stream, Triples* triples):
    if triples.subject and triples.predicate and triples.object:
        n = triples.n
        if triples.n == triples.limit:
            resize_triples(triples)
        triples.subjects[n] = triples.subject
        triples.predicates[n] = triples.predicate
        triples.objects[n] = triples.object
        triples.object = 0
        triples.n += 1
    else:
        print((triples.subject, triples.predicate, triples.object))
        raise Exception('Comma error at %i'%stream.i)
    return triples
