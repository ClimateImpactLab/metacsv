

import pandas as pd, numpy as np, xarray as xr
from pandas.compat import string_types
from collections import OrderedDict


class GraphIsCyclicError(ValueError):
  pass

class Container(object):
  
  @staticmethod
  def _validate_coords(coords):
    ''' Validate coords to test for cyclic graph '''

    if not hasattr(coords, 'iterkeys'):
      return OrderedDict(zip(list(coords), [None for _ in range(len(coords))]))

    base_coords = set()
    dependencies = OrderedDict([])
    visited = set()

    def find_coord_dependencies(coord):
      if coord in visited:
        if coord not in dependencies:
          raise GraphIsCyclicError
        return

      deps = coords.pop(coord)

      if deps is None:
        base_coords.add(coord)
        dependencies[coord] = None
        visited.add(coord)

      elif isinstance(deps, string_types):
        visited.add(coord)
        find_coord_dependencies(deps)
        dependencies[coord] = set([deps])

      else:
        visited.add(coord)
        dependencies[coord] = set()
        for ele in deps:
          find_coord_dependencies(ele)
          dependencies[coord].add(ele)

    while len(coords) > 0:
      find_coord_dependencies(next(coords.iterkeys()))

    return dependencies, base_coords


  def _update_coords(coords=None):

    if coords is None:
      if not pd.isnull(self.index.names).any():
        coords = self._validate_coords(self.index.names)
      
      elif len(self.index.names) == 1 and self.index.names[0] is None:
        self.index.names = ['index']
        self._coords = self._validate_coords(self.index.names)

      elif pd.isnull(self.index.names).all():
        self.index.names = [coord if coord is not None else 'level_{}'.format(i) for i, coord in enumerate(self.index.names)]
        self._coords = self._validate_coords(self.index.names)

    else:
      coords = self._validate_coords(coords)

    self._coords = coords


  def __init__(self, *args, **kwargs):
    self._update_coords(kwargs.pop('coords', None))




class DataFrame(Container, pd.DataFrame):
  '''
  MetaDoc.DataFrame, inherrited from pandas.DataFrame
  '''

  _metadata = [
    '_attrs',       # Metadata/documentation attributes
    '_variables',   # Column Names
    '_coords'       # Index Names
  ]

  @property
  def _constructor(self):
    return DataFrame

  @property
  def _constructor_sliced(self):
    return Series

  @property
  def _constructor_expanddims(self):
    return Panel

  def __init__(self, *args, **kwargs):
    self._attrs = kwargs.pop('attrs', {})
    
    coords = kwargs.pop('coords', None)
    
    pd.DataFrame.__init__(self, *args, **kwargs)
    Container.__init__(self, coords=coords, *args, **kwargs)
    
    

class Series(Container, pd.Series):
  '''
  MetaDoc.Series, inherrited from pandas.Series
  '''

  _metadata = [
    '_attrs',       # Metadata/documentation attributes
    '_coords'       # Index Names
  ]

  @property
  def _constructor(self):
    return Series

  @property
  def _constructor_expanddim(self):
    return DataFrame

  def __init__(self, *args, **kwargs):
    self._attrs = kwargs.pop('attrs', {})
    
    coords = kwargs.pop('coords', None)
    
    pd.Series.__init__(self, *args, **kwargs)
    Container.__init__(self, coords=coords, *args, **kwargs)
    
    