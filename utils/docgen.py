'''Run this script to generate documentation from the source code. In the
command line, from within the top-level koalas folder,
run `python3 utils/docgen.py`'''

from inspect import signature
import re
import types


def print_member_doc(obj, objname='', pretendname='', ignore_param=False):
    if objname.startswith('_'):
        return ''
    output = ''
    if type(obj) == types.ModuleType:
        objname = obj.__name__
        doc = obj.__doc__
        doc = '\n\n%s\n\n'%re.sub(r'\s*\n\s*', ' ', str(doc)) if doc else '\n\n'
        if getattr(obj, '_doc_pretend', False):
            output += print_member_doc(obj.__dict__.get(obj._doc_pretend),
                             obj._doc_pretend, pretendname=objname)
        else:
            if objname:
                output += ('## module *%s*:%s'%(pretendname or objname, doc))
            for name, member in obj.__dict__.items():
                if getattr(member, '__module__', '').endswith(objname) and type(member) is not types.ModuleType:
                    output += print_member_doc(getattr(obj, name), name)
                elif name == 'listfiles':
                    output += print_member_doc(getattr(obj, name), name)
            for name in getattr(obj, '_doc_follow', []):
                print(objname)
                param_ignore = objname.endswith('scripts')
                output += print_member_doc(getattr(obj, name), name, ignore_param=param_ignore)

    elif type(obj) == type:
        doc = obj.__doc__
        doc = '\n\n%s\n\n'%re.sub(r'\s*\n\s*', ' ', str(doc)) if doc else '\n\n'
        output += ('### class **%s**:%s'%(pretendname or objname, doc))
        for name, member in obj.__dict__.items():
            output += print_member_doc(member, name)

    elif type(obj) == types.FunctionType and objname == 'info':
        output += '### Available Lists:\n\n'
        output += koalas.lists.info('all') + '\n\n'

    elif type(obj) == types.FunctionType:
        doc = re.sub(r'\s*\n\s*', ' ', str(obj.__doc__ or '*No description yet*'))
        if ignore_param:
            sig = re.sub(r'\(.*?([\),])', r'(\1', str(signature(obj)))
        else:
            sig = re.sub(r'self(, )?', '', str(signature(obj)))
        output += ('- **%s** *%s*:\n\n     %s\n\n'%(pretendname or objname, sig, doc))

    return output

def make_TOC(document):
    sections = []
    for line in document.splitlines():
        if line.startswith('##'):
            name = line.lstrip('# ').rstrip(':')
            level = (len(line) - len(line.lstrip('# ')) - 3) * 4
            anchor = name.lower().replace(' ', '-').replace('*', '')
            sections.append((name, anchor, level))
    TOC = '## Contents\n\n'
    for (name, anchor, level) in sections:
        TOC += ' ' * level + '- [%s](#%s)\n'%(name, anchor)
    return TOC


if __name__ == '__main__':
    import grizzly

    with open('utils/readme_text.md') as f:
        docs = f.read()

    docs += print_member_doc(grizzly)
    TOC = make_TOC(docs)
    docs = docs.replace(r'{TOC}', TOC)

    with open('README.md', 'w') as f:
        f.write(docs)
