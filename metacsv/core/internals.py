

import pandas as pd, numpy as np, yaml
from .._compat import string_types, has_iterkeys, iterkeys
from .converters import convert_to_xarray, write_to_csv_object
from .exceptions import GraphIsCyclicError
from collections import OrderedDict
from pandas.core.base import FrozenList


class _BaseProperty(object):
  property_type = None # overload
  repr_order = []

  def __init__(self, data=None, container=None):
    self.__set__(data)

  def __repr__(self):
    return str(self)

  def __str__(self):
    if self._data is not None and len(self._data) > 0:
      repr_str = '' if len(self._data) == 0 else self.property_type
      for props, prop_data in self._data.items():
        repr_str += '\n    {: <10} {}'.format(props, prop_data)
      return repr_str
    else:
      return '<Empty {}>'.format(self.property_type)

  def __iter__(self):
    if self._data is not None:
      for k, v in self._data.items():
        yield k, v

  def pop(self, key, *default):
    if self._data is not None:
      if len(default) == 0:
        return self._data.pop(key)
      elif len(default) == 1:
        return self._data.pop(key, default[0])
      else:
        raise ValueError('pop() takes exactly 2 arguments ({} given)'.format(len(default)+1))

    else:
      raise KeyError('{} not yet assigned.'.format(self.property_type))

  def get(self, key, *default):
    if self._data is not None:
      if len(default) == 0:
        return self._data.get(key)
      elif len(default) == 1:
        return self._data.get(key, default[0])
      else:
        raise ValueError('get() takes exactly 2 arguments ({} given)'.format(len(default)+1))

    else:
      raise KeyError('{} not yet assigned.'.format(self.property_type))

  def update(self, value):
    if self._data is not None:
      if isinstance(value, _BaseProperty):
        self._data.update(value._data)
      elif has_iterkeys(value):
        if len(value) > 0:
          self._data.update(value)
    if isinstance(value, None):
      return
    if isinstance(value, dict):
      if len(value) > 0:
        self._data = value


  def __getitem__(self, key):
    return self._data[key]

  def __setitem__(self, key, value):
    if isinstance(value, _BaseProperty):
      self._data[key] = value._data
    else:
      self._data[key] = value

  def __eq__(self, other):
    if hasattr(other, '_data'):
      return self._data == other._data
    if other is None and (self._data is None or len(self._data) == 0):
      return True
    return False

  def __ne__(self, other):
    return not self.__eq__(other)

  def __contains__(self, key):
    if self._data is None:
      return False
    return key in self._data

  def items(self):
    if self._data is not None:
      for k, v in self._data.items():
        yield (k,v)

  def copy(self):
    return type(self)(self)

  def __get__(self, data):
    if not hasattr(self, '_data'):
      self._data = None

    if self._data is None:
      return None

    return self._data

  def __set__(self, value):
    if value is None:
      self._data = None
    elif isinstance(value, _BaseProperty):
      self._data = value._data
    else:
      if isinstance(value, dict) or isinstance(value, OrderedDict):
        self._data = value
      else:
        raise TypeError

  def __del__(self):
    del self._data



class Attributes(_BaseProperty):
  property_type = 'Attributes'


class Variables(_BaseProperty):
  property_type = 'Variables'


class Coordinates(object):
  '''
  Manages coordinate system for MetaCSV data containers
  '''

  property_type = 'Coordinates'

  def __init__(self, coords=None, container=None):
    
    if container is not None:
      if not (isinstance(container, Container) or isinstance(container, pd.DataFrame) or isinstance(container, pd.Series)):
        raise TypeError('__init__ data argument must be a metacsv or pandas DataFrame or Series')

    self._container = container
    self.__set__(coords)

  def __set__(self, coords):
    self._coords            = None
    self._base_coords       = None
    self._base_dependencies = None

    if isinstance(coords, Coordinates) and (coords._coords is None or (len(coords._coords) == 0)):
      return
    elif coords is None or (len(coords) == 0):
      return
    elif isinstance(coords, Coordinates):
      _coords             = coords._coords
      _base_coords        = coords._base_coords
      _base_dependencies  = coords._base_dependencies
    else:
      _coords, _base_coords, _base_dependencies = self.parse_coords_definition(coords)

    self._send_coords_in_cols_to_index(_coords)
    self._validate_coords_against_data(coords=_coords)

    self._coords             = _coords
    self._base_coords        = _base_coords
    self._base_dependencies  = _base_dependencies


  def __repr__(self):
    coords_str = 'Coordinates'
    if self._coords is not None:
      for base in self._base_coords:
        coords_str += '\n' + self._repr_coord(base, base=True)
      for coord in [c for c in self._coords if not c in self._base_coords]:
        coords_str += '\n' + self._repr_coord(coord, base=False)
      return coords_str
    else:
      return '<Empty {}>'.format(self.property_type)

  def __iter__(self):
    if self._coords is not None:
      for k in self._coords.keys():
        yield k


  # TODO:
  # ensure compatability with PY3 and 
  # pd._compat utilities
  def items(self):
    if self._coords is not None:
      for k, v in self._coords.items():
        yield (k,v)


  def __eq__(self, other):
    if isinstance(other, Coordinates):
      return (self._coords == other._coords) and (self._base_coords == other._base_coords)
    elif (other is None) and (self._coords is None):
      return True
    return False

  def __ne__(self, other):
    return not self.__eq__(other)

  def __getitem__(self, key):
    return self._coords[key]

  def _repr_coord(self, coord, base=False, maxlen=50):
    if self._container is None:
      datastr = ''
    else:
      datastr = ''
      if isinstance(self._container.index, pd.MultiIndex):
        coord_data = self._container.index.levels[self._container.index.names.index(coord)]
      else:
        coord_data = self._container.index.values

      datastr += ' {} '.format(coord_data.dtype)

      for i, ind in enumerate(coord_data):
        if len(datastr) + len(str(ind)) + 5 > maxlen:
          return datastr + '...'

        if i > 0:
          datastr += ', '

        datastr += '{}'.format(ind)

    coordstr = '  * ' if base else '    '
    coordstr += '{: <10}'.format(coord)
    coordstr += ' ({})'.format(coord if base else ','.join(list(map(str, self._coords[coord]))))
    coordstr += datastr

    return coordstr

  def copy(self):
    return Coordinates(None if self._coords is None else self._coords.copy())

  @property
  def base_coords(self):
    return self._base_coords

  @staticmethod
  def parse_coords_definition(coords=None):
    ''' Validate coords to test for cyclic graph '''
    if coords is None:
      return None, None, None

    if isinstance(coords, string_types):
      return OrderedDict([(coords, None)]), FrozenList([coords]), {coords: set([coords])}

    elif not has_iterkeys(coords):
      if isinstance(coords, Coordinates):
        coords = coords._coords
      coords = OrderedDict(list(zip(list(coords), [None for _ in range(len(coords))])))
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

  def _get_coords_from_data(self):

    if not pd.isnull(self._container.index.names).any():
      coords, base_coords, base_dependencies = self.parse_coords_definition(self._container.index.names)
    
    elif len(self._container.index.names) == 1 and self._container.index.names[0] is None:
      self._container.index.names = ['index']
      coords, base_coords, base_dependencies = self.parse_coords_definition(self._container.index.names)

    elif pd.isnull(self._container.index.names).any():
      self._container.index.names = [coord if coord is not None else 'level_{}'.format(i) for i, coord in enumerate(self._container.index.names)]
      coords, base_coords, base_dependencies = self.parse_coords_definition(self._container.index.names)

    return coords, base_coords, base_dependencies

  def set_coords_from_data(self):
    self._coords, self._base_coords, self._base_dependencies = self._get_coords_from_data()


  def update_coords(self, coords=None):  # This needs some testing!!

    if coords is None:
      coords, base_coords, base_dependencies = self._get_coords_from_data()

    self._coords.update(coords)
    self._send_coords_in_cols_to_index()

  def _send_coords_in_cols_to_index(self, coords=None, container=None):
    coords = coords if coords is not None else self._coords
    if coords is None:
      return 

    container   = container   if container   is not None else self._container

    if self._container is None:
      return

    if hasattr(container, 'columns') and hasattr(container, 'set_index'):
      if len(container.index.names) == 1 and (container.index.names[0] is None):
        append=False
      else:
        append=True

      set_coords = [c for c in coords if (c not in container.index.names) and (c in container.columns)]
      if len(set_coords) > 0:
        container.set_index(set_coords, inplace=True, append=append)


  def update(self, coords):

    self._prune()

    if not hasattr(self, '_coords'):
      _coords = {}
    else:
      _coords = self._coords.copy()

    _coords.update(coords)
    coords, base_coords, base_dependencies = self.parse_coords_definition(_coords)
    self._validate_coords_against_data(coords=coords)

    assert len(base_coords) > 0, "Index must have at least one base coordinate"

    self._coords = coords
    self._base_coords = base_coords
    self._base_dependencies = base_dependencies

  @staticmethod
  def _get_available_coords(container):
    available_coords = []
    for dim in ['index', 'columns']:
      if hasattr(container, dim):
        available_coords.extend([i for i in container.__getattr__(dim).names if i is not None])

    return available_coords

  def _prune(self, coords=None, container=None):
    coords = coords if coords is not None else self._coords
    if coords is None:
      return

    container   = container   if container   is not None else self._container

    available_coords = self._get_available_coords(container
)
    for c in coords:
      if c not in available_coords:
        coords.pop(c)

    return coords

  def _validate_coords_against_data(self, coords=None, container=None):
    if coords is None:
      return

    container = container if container is not None else self._container
    if container is None:
      return

    for c in coords.keys():
      assert c in container.index.names, "Coordinate '{c}' not found in container index".format(c=c)

    for c in container.index.names:
      assert c in coords, "Data index '{c}' not found in supplied coordinates".format(c=c)
    



class Container(object):

  def __init__(self, coords=None, variables=None, attrs=None, *args, **kwargs):
    '''
    Initialization method for Container objects

    :param argumentName: an example argument.
    :type argumentName: string
    :param anOptionalArg: an optional argument.
    :type anOptionalArg: string
    :returns: New instance of :class:`Container`
    :rtype: Container

    '''

    self.coords = coords
    self.attrs = attrs
    self.variables = variables


  # Container Properties

  ## coords

  @property
  def coords(self):
    '''Coordinates property of a metacsv Container'''
    if not hasattr(self, '_coords'):
      self._coords = Coordinates()

    return self._coords

  @coords.setter
  def coords(self, value):
    if value is None:
      self._coords = Coordinates()
    else:
      self._coords = Coordinates(value, container=self)

  @coords.deleter
  def coords(self):
    self._coords = None

  @property
  def base_coords(self):
    if not hasattr(self, '_coords'):
      self.coords = Coordinates()

    if self.coords == None:
      return None

    return self._coords._base_coords

  ## attrs

  @property
  def attrs(self):
    '''Coordinates property of a metacsv Container'''
    if not hasattr(self, '_attrs'):
      self._attrs = Attributes()

    return self._attrs

  @attrs.setter
  def attrs(self, value):
    if value is None:
      self._attrs = Attributes()
    else:
      self._attrs = Attributes(value, container=self)

  @attrs.deleter
  def attrs(self):
    self._attrs = None


  ## variables

  @property
  def variables(self):
    '''Coordinates property of a metacsv Container'''
    if not hasattr(self, '_variables'):
      self._variables = Variables()

    if self._variables == None:
      return

    return self._variables

  @variables.setter
  def variables(self, value):
    if value is None:
      self._variables = Variables()
    else:
      self._variables = Variables(value, container=self)

  @variables.deleter
  def variables(self):
    self._variables = None


  # Special Container Methods

  def add_coords(self):
    if self.coords == None:
      self.coords = Coordinates(container=self)

    self.coords.set_coords_from_data()

  def _get_coord_data_from_index(self, coord):
    return self.index.get_level_values(coord)

  @staticmethod
  def get_unique_multiindex(series):
    return series.iloc[np.unique(series.index.values, return_index=True)[1]]

  @staticmethod
  def stringify_index_names(series):
    series.index.names = list(map(str, series.index.names))
    return series

  @staticmethod
  def strip_special_attributes(args, kwargs):

    attrs = kwargs.pop('attrs', {}).copy()

    def update_property(p_data, data, func=lambda x: x):
      if hasattr(data, 'copy'):
        data = data.copy()
      parsed = func(data)
      p_data.update(parsed)

    def strip_property(prop, func = lambda x: x):
      p_data = {}

      update_property(p_data, attrs.pop(prop, {}), func)
      update_property(p_data, kwargs.pop(prop, {}), func)
      
      if len(p_data) == 0:
        p_data = None

      return p_data

    coords = strip_property('coords', lambda x: Coordinates.parse_coords_definition(x)[0])
    variables = strip_property('variables')

    special = {}

    if (coords is not None) and (len(coords) > 0):
      special['coords'] = coords

    if (variables is not None) and (len(variables) > 0):
      special['variables'] = variables

    if (attrs is not None) and (len(attrs) > 0):
      special['attrs'] = attrs

    return args, kwargs, special



  # Container formatting

  def _print_format(self):
    metacsv_str = '<{} {}>'.format(type(self).__module__ + '.' + type(self).__name__, self.shape)
    data_str = self.pandas_parent.__str__(self)
    postscript = '\n'.join([str(p) for p in [self.coords, self.variables, self.attrs] if p != None])
    return (metacsv_str + '\n' + data_str + ('\n\n' if len(postscript)>0 else '') + postscript)

  def __repr__(self):
    return str(self)

  def __str__(self):
    return self._print_format()


  # Container conversion & I/O

  def to_csv(self, fp, *args, **kwargs):
    if isinstance(fp, string_types):
      with open(fp, 'w+') as fp2:
        write_to_csv_object(self, fp2, *args, **kwargs)
    else:
      write_to_csv_object(self, fp, *args, **kwargs)

  def to_pandas(self):
    ''' return a copy of the data in a pandas.DataFrame object '''
    return self.pandas_parent(self)

  def to_xarray(self):
    ''' return an xarray container '''
    return convert_to_xarray(self)

  def to_dataarray(self):
    ''' return an xarray.DataArray (if DataFrame, columns will be unstacked and treated as a coordinate) '''

    if len(self.shape) > 2:
      raise NotImplementedError("to_dataset not yet implemented for Panel data")

    if len(self.shape) == 1:
      return self.to_xarray()

    if len(self.shape) == 2:
      self.columns.names = [c if c is not None else 'ind_{}'.format(len(self.index.names) + i) for i, c in enumerate(self.columns.names)]
      
      return self.unstack(self.columns.names[0]).to_dataarray()
