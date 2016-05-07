

import pandas as pd, numpy as np, xarray as xr
from pandas.compat import string_types
from collections import OrderedDict
from pandas.core.base import FrozenList


class GraphIsCyclicError(ValueError):
  pass

class Container(object):
  
  @staticmethod
  def _validate_coords(coords):
    ''' Validate coords to test for cyclic graph '''

    if not hasattr(coords, 'iterkeys'):
      coords = OrderedDict(zip(list(coords), [None for _ in range(len(coords))]))
      return coords, FrozenList(coords.keys())

    base_coords = []
    dependencies = OrderedDict([])
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

    return dependencies, FrozenList(base_coords)


  def _update_coords(self, coords=None):
    if not hasattr(self, '_coords'):
      _coords = {}
    else:
      _coords = self._coords.copy()

    if coords is None:
      if not pd.isnull(self.index.names).any():
        coords, base_coords = self._validate_coords(self.index.names)
      
      elif len(self.index.names) == 1 and self.index.names[0] is None:
        self.index.names = ['index']
        coords, base_coords = self._validate_coords(self.index.names)

      elif pd.isnull(self.index.names).all():
        self.index.names = [coord if coord is not None else 'level_{}'.format(i) for i, coord in enumerate(self.index.names)]
        coords, base_coords = self._validate_coords(self.index.names)

    else:
      _coords.update(coords)
      coords, base_coords = self._validate_coords(_coords)

    self._coords = coords
    self._base_coords = base_coords


  def _get_coords_data_from_index(self):

    coords = OrderedDict()

    get_coord = lambda x: self.index.get_level_values(x)

    for coord in self._base_coords:
      coords[str(coord)] = get_coord(coord).values

    for coord in [k for k in self._coords.keys() if k not in self._base_coords]:
      deps = self._coords[coord]
      coords[str(coord)] = xr.DataArray.from_series(pd.Series(get_coord(coord), index=pd.MultiIndex.from_tuples(zip(*tuple(get_coord(dep) for dep in deps)), names=map(str, deps))))

    return coords


  def to_dataarray(self):

    if len(self.shape) > 2:
      raise NotImplementedError("to_dataarray not yet implemented for Panel data")

    if len(self.shape) == 1:
      coords = self._get_coords_data_from_index()
      return xr.DataArray.from_series(pd.Series(self.values, index=pd.MultiIndex.from_tuples(zip(*tuple([get_coord(coord) for coord in self._base_coords])), names=map(str, self._base_coords))))

    if len(self.shape) == 2:
      return self.unstack(self.columns.names[0]).to_dataarray()

  def to_dataset(self):

    if len(self.shape) > 2:
      raise NotImplementedError("to_dataset not yet implemented for Panel data")

    if len(self.shape) == 1:
      coords = self._get_coords_data_from_index()
      return xr.Dataset(
        data_vars = {'var_1': data_xr.DataArray.from_series(pd.Series(self.values, index=pd.MultiIndex.from_tuples(zip(*tuple([get_coord(coord) for coord in self._base_coords])), names=map(str, self._base_coords))))},
        coords = coords,
        attrs = self._attrs)

    if len(self.shape) == 2:
      coords = self._get_coords_data_from_index()
      return xr.Dataset(data_vars=OrderedDict([(col, self[col].values) for col in self.columns]), coords=coords, attrs=self._attrs)



  def __init__(self, *args, **kwargs):
    coords = kwargs.pop('coords', None)
    self._update_coords(coords)




class DataFrame(Container, pd.DataFrame):
  '''
  MetaDoc.DataFrame, inherrited from pandas.DataFrame
  '''

  _metadata = [
    '_attrs',       # Metadata/documentation attributes
    '_variables',   # Column Names
    '_coords',      # Index Names
    '_base_coords'  # "Base" Index Names
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
    '_coords',      # Index Names
    '_base_coords'  # "Base" Index Names
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
    
    


class Panel(pd.Panel):

  _metadata = [
    '_attrs',       # Metadata/documentation attributes
    '_coords',      # Index Names
    '_base_coords'  # "Base" Index Names
  ]

  @property
  def _constructor(self):
    return Panel

  @property
  def _constructor_sliced(self):
    return DataFrame

  def __init__(self, *args, **kwargs):
    self._attrs = kwargs.pop('attrs', {})
    
    coords = kwargs.pop('coords', None)
    
    pd.Series.__init__(self, *args, **kwargs)
    Container.__init__(self, coords=coords, *args, **kwargs)