

import pandas as pd, numpy as np, xarray as xr, yaml
from .._compat import string_types, has_iterkeys, iterkeys
from .exceptions import GraphIsCyclicError
from collections import OrderedDict
from pandas.core.base import FrozenList


class _BaseProperty(object):
  property_type = None # overload
  repr_order = []

  def __init__(self, data, container=None):
    self._data = data
  def __repr__(self):
    repr_str = None if len(self._data) == 0 else self.property_type
    for props, prop_data in self._data.items():
      repr_str += '\n    {: <10} {}'.format(props, prop_data)
    return repr_str


  def __get__(self, data):
    if not hasattr(self, '_data'):
      self._data = None

    if self._data is None:
      return None
    return self._data

  def __set__(self, value):
    if value is None:
      self._data = None
    else:
      self._data = value

  def __del__(self):
    del self._data

  @classmethod
  def get_property(cls):
    return property(cls.__get__, cls.__set__, cls.__del__, cls.__doc__)


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
    
    if container is None and coords is None:
      raise ValueError('Must supply coords or data to __init__')
    
    elif container is None:
      self._container = None
      self.__set__(coords)

    elif isinstance(container, Container) or isinstance(container, pd.DataFrame) or isinstance(container, pd.Series):
      self._container = container
      
      if coords is None:
        self._set_coords_from_data()
      else:
        self.__set__(coords)
        
    else:
      raise TypeError('__init__ data argument must be a metacsv or pandas DataFrame or Series')

  def __set__(self, coords):

    if isinstance(coords, Coordinates):
      _coords             = coords._coords
      _base_coords        = coords._base_coords
      _base_dependencies  = coords._base_dependencies
    else:
      _coords, _base_coords, _base_dependencies = self._parse_coords_definition(coords)

    self._set_coords_from_columns(_coords)
    self._validate_coords_against_data(coords=_coords)

    self._coords             = _coords
    self._base_coords        = _base_coords
    self._base_dependencies  = _base_dependencies


  def __repr__(self):
    coords_str = 'Coordinates'
    for base in self._base_coords:
      coords_str += '\n' + self._repr_coord(base, base=True)
    for coord in [c for c in self._coords if not c in self._base_coords]:
      coords_str += '\n' + self._repr_coord(coord, base=False)
    return coords_str

  def __iter__(self):
    for k in self._coords.keys():
      yield k

  def items(self):
    for k, v in self._coords.items():
      yield (k,v)

  def __eq__(self, other):
    if isinstance(other, Coordinates):
      return (self._coords == other._coords) and (self._base_coords == other._base_coords)
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
    coordstr += ' ({})'.format(coord if base else ','.join(self._coords[coord]))
    coordstr += datastr

    return coordstr

  def copy(self):
    return Coordinates(self._coords.copy(), container=self._container)

  def get_base_coords(self):
    return self._base_coords

  @property
  def base_coords(self):
    return self.get_base_coords()


  @staticmethod
  def _parse_coords_definition(coords):
    ''' Validate coords to test for cyclic graph '''
    if isinstance(coords, string_types):
      return OrderedDict([(coords, None)]), FrozenList([coords]), {coords: set([coords])}

    elif not has_iterkeys(coords):
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
      coords, base_coords, base_dependencies = self._parse_coords_definition(self._container.index.names)
    
    elif len(self._container.index.names) == 1 and self._container.index.names[0] is None:
      self._container.index.names = ['index']
      coords, base_coords, base_dependencies = self._parse_coords_definition(self._container.index.names)

    elif pd.isnull(self._container.index.names).any():
      self._container.index.names = [coord if coord is not None else 'level_{}'.format(i) for i, coord in enumerate(self._container.index.names)]
      coords, base_coords, base_dependencies = self._parse_coords_definition(self._container.index.names)

    return coords, base_coords, base_dependencies

  def _set_coords_from_data(self):
    self._coords, self._base_coords, self._base_dependencies = self._get_coords_from_data()


  def update_coords(self, coords=None):  # This needs some testing!!

    if coords is None:
      coords, base_coords, base_dependencies = self._get_coords_from_data()

    self._coords.update(coords)
    self._set_coords_from_columns()

  def _set_coords_from_columns(self, coords=None, container=None):
    coords = coords if coords is not None else self._coords
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
    coords, base_coords, base_dependencies = self._parse_coords_definition(_coords)
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
    container   = container   if container   is not None else self._container

    available_coords = self._get_available_coords(container)

    for c in coords:
      if c not in available_coords:
        coords.pop(c)

    return coords

  def _validate_coords_against_data(self, coords, container=None):
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

    self.coords = Coordinates(coords, container=self)
    self.attrs = Attributes(coords, container=self)
    self.variables = Variables(coords, container=self)


  @property
  def coords(self):
    '''Coordinates property of a metacsv Container'''
    if not hasattr(self, '_coords'):
      self._coords = None

    if self._coords is None:
      return None
    return self._coords

  @coords.setter
  def coords(self, value):
    if value is None:
      self._coords = None
    else:
      self._coords = Coordinates(value, container=self)

  @coords.deleter
  def coords(self):
    self._coords = None


  @property
  def attrs(self):
    '''Coordinates property of a metacsv Container'''
    if not hasattr(self, '_attrs'):
      self._attrs = None

    if self._attrs is None:
      return None
    return self._attrs

  @attrs.setter
  def attrs(self, value):
    if value is None:
      self._attrs = None
    else:
      self._attrs = Attributes(value, container=self)

  @attrs.deleter
  def attrs(self):
    self._attrs = None


  @property
  def variables(self):
    '''Coordinates property of a metacsv Container'''
    if not hasattr(self, '_variables'):
      self._variables = None

    if self._variables is None:
      return None
    return self._variables

  @variables.setter
  def variables(self, value):
    if value is None:
      self._variables = None
    else:
      self._variables = Variables(value, container=self)

  @variables.deleter
  def variables(self):
    self._variables = None

  # @staticmethod
  # def pull_attribute(kwargs, attrs, attr):
  #   data = None
  #   if attr in kwargs:
  #     data = kwargs.pop(attr)
  #   attrs = kwargs.get(attrs)

  def _get_coord_data_from_index(self, coord):
    return self.index.get_level_values(coord)


  def _get_coords_dataarrays_from_index(self):

    coords = OrderedDict()

    for coord in self.base_coords:
      coords[str(coord)] = self._get_coord_data_from_index(coord).values

    for coord in [k for k in self.coords if k not in self.base_coords]:
      deps = self.coords[coord]
      coords[str(coord)] = xr.DataArray.from_series(pd.Series(self._get_coord_data_from_index(coord), index=pd.MultiIndex.from_tuples(list(zip(*tuple(self._get_coord_data_from_index(dep) for dep in deps))), names=list(map(str, deps)))))

    return coords

  @staticmethod
  def get_unique_multiindex(series):
    return series.iloc[np.unique(series.index.values, return_index=True)[1]]

  @staticmethod
  def strip_special_attributes(args, kwargs):
    attrs = kwargs.pop('attrs', {})

    coords = None

    c1 = attrs.pop('coords', None)
    c2 = kwargs.pop('coords', None)

    if c1 is not None:
      coords = c1

    if c2 is not None:
      if coords is None:
        coords = c2
      else:
        coords.update(c2)

    variables = attrs.pop('variables', {})
    variables.update(kwargs.pop('variables', {}))

    special = {
      'attrs': attrs,
      'variables': variables,
      'coords': coords
    }

    return args, kwargs, special

  def _write_csv_to_file_object(self, fp, *args, **kwargs):
    attr_dict = {}
    attr_dict.update(dict(self.attrs))

    if self.coords is not None:
      attr_dict.update({'coords': dict(self.coords.items())})

    if hasattr(self, 'variables'):
      attr_dict.update({'variables': dict(self.variables._variables)})

    fp.write('---\n')
    fp.write(yaml.safe_dump(attr_dict, default_flow_style=False, allow_unicode=True))
    fp.write('---\n')
    self.pandas_parent.to_csv(self, fp, *args, **kwargs)


  def to_csv(self, fp, *args, **kwargs):
    if isinstance(fp, string_types):
      with open(fp, 'w+') as fp2:
        self._write_csv_to_file_object(fp2, *args, **kwargs)
    else:
      self._write_csv_to_file_object(fp, *args, **kwargs)

  def to_xarray(self):

    if len(self.shape) > 2:
      raise NotImplementedError("to_xarray not yet implemented for Panel data")

    if len(self.shape) == 1:
      coords = self._get_coords_dataarrays_from_index()
      return xr.DataArray.from_series(pd.Series(
        self.values, 
        index=pd.MultiIndex.from_tuples(
          list(zip(*tuple([self._get_coord_data_from_index(coord) for coord in self.base_coords]))), 
          names=list(map(str, self.base_coords)))))

    if len(self.shape) == 2:

      ds = xr.Dataset()

      for coord in self.base_coords:
        ds.coords[coord] = self.index.get_level_values(coord).unique()


      for coord in self.coords:
        if coord in self.base_coords:
          continue

        ds.coords[coord] = xr.DataArray.from_series(self.get_unique_multiindex(self.reset_index([c for c in self.index.names if c not in self._coords._base_dependencies[coord]], drop=False, inplace=False)[coord]))

      for col in self.columns:
        ds[col] = xr.DataArray.from_series(self.get_unique_multiindex(self.reset_index([c for c in self.index.names if not c in self.base_coords], drop=False, inplace=False)[col]))

      ds.attrs.update(self.attrs)

      return ds

  def to_dataarray(self):

    if len(self.shape) > 2:
      raise NotImplementedError("to_dataset not yet implemented for Panel data")

    if len(self.shape) == 1:
      return self.to_xarray()

    if len(self.shape) == 2:
      self.columns.names = [c if c is not None else 'ind_{}'.format(len(self.index.names) + i) for i, c in enumerate(self.columns.names)]
      
      return self.unstack(self.columns.names[0]).to_dataarray()


  @property
  def metacsv_str(self):
    return '<{} {}>'.format(type(self).__module__ + '.' + type(self).__name__, self.shape)

  @property
  def coords_str(self):
    if self.coords is None:
      return ''
    else:
      return self.coords.__repr__()

  @property
  def var_str(self):
    if hasattr(self, 'variables') and self.variables is not None:
      return self.variables.__repr__()
    else:
      return ''

  @property
  def attr_str(self):
    if hasattr(self, 'attrs') and self.attrs is not None:
      return self.attrs.__repr__()
    else:
      return ''

    return (
      '' if len(self.attrs) == 0 else 
      'Attributes\n    ' + '\n    '.join(list(map(lambda x: '{}: {}'.format(*x), self.attrs.items())))
      )
    
  def _print_format(self):
    data_str = self.pandas_parent.__str__(self)
    postscript = '\n'.join([p for p in [self.coords_str, self.var_str, self.attr_str] if len(p) > 0])
    return (self.metacsv_str + '\n' + data_str + ('\n\n' if len(postscript)>0 else '') + postscript)

  def __repr__(self):
    return str(self)

  def __str__(self):
    return self._print_format()


  def to_pandas(self):
    ''' return a copy of the data in a pandas.DataFrame object '''
    return self.pandas_parent(self)
