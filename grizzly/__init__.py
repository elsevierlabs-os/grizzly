from .base import Base
from .graph import Graph
from .table import Table
from .repository import Repository
from .prefix import Prefix, common_prefixes
from .factories import read_turtle, read_json, read_csv, read_ntriples, read_remote
from .utils import concat

_doc_follow = ['read_turtle', 'read_csv', 'read_json', 'read_ntriples', 'read_remote', 'Base',
'Graph', 'Table', 'Repository']
