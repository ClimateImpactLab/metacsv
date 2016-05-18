

from .._compat import string_types, has_iterkeys, iterkeys
from collections import OrderedDict
from pandas.core.base import FrozenList

class GraphIsCyclicError(ValueError):
  pass


class Coordinates(object):
  '''
  Manages coordinate system for MetaCSV data containers

  :param argumentName: an example argument.
  :type argumentName: string
  :param anOptionalArg: an optional argument.
  :type anOptionalArg: string
  :returns: New instance of :class:`Coordinates`
  :rtype: Coordinates
  '''

  def __init__(self, coords={}):
    self.__set__(coords)

  def __get__(self):
    return self._coords

  def __set__(self, coords):
    self._coords, self._base_coords, self._base_dependencies = self._validate_coords(coords)

  def copy(self):
    return Coordinates(self._coords.copy())

  def get_base_coords(self):
    return self._base_coords

  @property
  def base_coords(self):
    return self.get_base_coords()


  @staticmethod
  def _validate_coords(coords):
    ''' Validate coords to test for cyclic graph '''

    if isinstance(coords, string_types):
      return OrderedDict([(coords, None)]), FrozenList([coords]), {coords: set([coords])}

    elif not has_iterkeys(coords):
      coords = OrderedDict(zip(list(coords), [None for _ in range(len(coords))]))
      return coords, FrozenList(coords.keys()), {c: set([c]) for c in coords.keys()}

    base_coords = []
    dependencies = OrderedDict([])
    base_deps = {}
    visited = set()

    def find_coord_dependencies(coord):
      if coord in visited:
        if coord not in dependencies:
          raise GraphIsCyclicError
        return

      deps = coords.pop(coord)


      if deps is None:
        base_coords.append(coord)
        dependencies[coord] = None
        base_deps[coord] = set([coord])
        visited.add(coord)

      elif isinstance(deps, string_types):
        visited.add(coord)
        find_coord_dependencies(deps)
        dependencies[coord] = set([deps])
        base_deps[coord] = base_deps[deps]

      else:
        visited.add(coord)
        dependencies[coord] = set()
        base_deps[coord] = set()
        for ele in deps:
          find_coord_dependencies(ele)
          dependencies[coord].add(ele)
          base_deps[coord] |= base_deps[ele]

    while len(coords) > 0:
      find_coord_dependencies(next(iterkeys(coords)))

    return dependencies, FrozenList(base_coords), base_deps


  def _update(self, coords):
    if not hasattr(self, '_coords'):
      _coords = {}
    else:
      _coords = self._coords.copy()

    _coords.update(coords)
    coords, base_coords, base_dependencies = self._validate_coords(_coords)

    assert len(base_coords) > 0, "Index must have at least one base coordinate"

    self._coords = coords
    self._base_coords = base_coords
    self._base_dependencies = base_dependencies


