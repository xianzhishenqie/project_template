from .config import Resource
from .execute import Dumper, Loader
from .meta import ResolveConflictType, RelationType


def dumps(root_objs, to_dir=None):
    return Dumper(root_objs).dumps(to_dir)


def loads(root, index, data, from_dir=None):
    return Loader().loads(root, index, data, from_dir)
