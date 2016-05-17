

import pandas as pd, numpy as np, xarray as xr, yaml
from .._compat import string_types
from collections import OrderedDict
from pandas.core.base import FrozenList

from metacsv.core.internals import Coordinates


class Container(object):

  def __init__(self, coords=None, *args, **kwargs):
    '''
    Initialization method for Container objects

    :param argumentName: an example argument.
    :type argumentName: string
    :param anOptionalArg: an optional argument.
    :type anOptionalArg: string
    :returns: New instance of :class:`Container`
    :rtype: Container

    '''

    if coords is None:
      coords = dict(('index_{}'.format(i) if coord is None else coord, None) for i, coord in enumerate(self.index.names))
    self._coords = Coordinates(coords)

  @property
  def coords(self):
    return self._coords.__get__()

  @property
  def base_coords(self):
    return self._coords.base_coords

  # @staticmethod
  # def pull_attribute(kwargs, attrs, attr):
  #   data = None
  #   if attr in kwargs:
  #     data = kwargs.pop(attr)
  #   attrs = kwargs.get(attrs)

  @property
  def metacsv_str(self):
    return '<{} {}>'.format(type(self).__module__ + '.' + type(self).__name__, self.shape)

  @property
  def coords_str(self):
    coords_str = 'Coordinates'
    for base in self.base_coords:
      coords_str += '\n' + self.repr_coord(base, base=True)
    for coord in [c for c in self.coords if not c in self.base_coords]:
      coords_str += '\n' + self.repr_coord(coord, base=False)
    return coords_str

  @property
  def attr_str(self):
    return (
      '' if len(self.attrs) == 0 else 
      '\nAttributes\n    ' + '\n    '.join(map(lambda x: '{}: {}'.format(*x), self.attrs.items()))
      )

  def repr_coord(self, coord, base=False, maxlen=50):
    if isinstance(self.index, pd.MultiIndex):
      coord_data = self.index.levels[self.index.names.index(coord)]
    else:
      coord_data = self.index.values

    coordstr = '  * ' if base else '    '
    coordstr += '{: <10}'.format(coord)
    coordstr += ' ({})'.format(coord if base else ','.join(self.coords[coord]))
    coordstr += ' {} '.format(coord_data.dtype)

    for i, ind in enumerate(coord_data):
      if len(coordstr) + len(str(ind)) + 5 > maxlen:
        return coordstr + '...'

      if i > 0:
        coordstr += ', '

      coordstr += '{}'.format(ind)

    return coordstr

  def _get_coord_data_from_index(self, coord):
    return self.index.get_level_values(coord)


  def _get_coords_dataarrays_from_index(self):

    coords = OrderedDict()

    for coord in self.base_coords:
      coords[str(coord)] = self._get_coord_data_from_index(coord).values

    for coord in [k for k in self.coords.keys() if k not in self.base_coords]:
      deps = self.coords[coord]
      coords[str(coord)] = xr.DataArray.from_series(pd.Series(self._get_coord_data_from_index(coord), index=pd.MultiIndex.from_tuples(zip(*tuple(self._get_coord_data_from_index(dep) for dep in deps)), names=map(str, deps))))

    return coords

  def update_coords(self, coords=None):  # This needs some testing!!

    if coords is None:
      if not pd.isnull(self.index.names).any():
        coords, base_coords, base_dependencies = self._coords._validate_coords(self.index.names)
      
      elif len(self.index.names) == 1 and self.index.names[0] is None:
        self.index.names = ['index']
        coords, base_coords, base_dependencies = self._coords._validate_coords(self.index.names)

      elif pd.isnull(self.index.names).any():
        self.index.names = [coord if coord is not None else 'level_{}'.format(i) for i, coord in enumerate(self.index.names)]
        coords, base_coords, base_dependencies = self._coords._validate_coords(self.index.names)

    self._coords._update(coords)


    if hasattr(self, 'columns') and hasattr(self, 'set_index'):
      if len(self.index.names) == 1 and (self.index.names[0] is None):
        append=False
      else:
        append=True

      set_coords = [c for c in self.coords if (c not in self.index.names) and (c in self.columns)]
      if len(set_coords) > 0:
        self.set_index(set_coords, inplace=True, append=append)


  @staticmethod
  def get_unique_multiindex(series):
    return series.iloc[np.unique(series.index.values, return_index=True)[1]]

  def _write_csv_to_file_object(self, fp, *args, **kwargs):
    attr_dict = {}
    attr_dict.update(dict(self.attrs))
    attr_dict.update({'coords': dict(self.coords)})

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
          zip(*tuple([self._get_coord_data_from_index(coord) for coord in self.base_coords])), 
          names=map(str, self.base_coords))))

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


class Attributes(object):
  def __init__(self, attrs):
    self.__set__(attrs)
  def __set__(self, attrs):
    self._attrs = attrs
  def __get__(self):
    return self._attrs


class Variables(object):
  def __init__(self, variables):
    self.__set__(variables)
  def __set__(self, variables):
    self._variables = variables
  def __get__(self):
    return self._variables


class Series(Container, pd.Series):
  '''
  metacsv.Series, inherrited from pandas.Series
  '''

  _metadata = [
    
    'attrs',        # Metadata/documentation attributes
    '_coords'       # Coordinates
  ]

  pandas_parent = pd.Series

  @property
  def _constructor(self):
    return Series

  @property
  def _constructor_expanddim(self):
    return DataFrame

  def __init__(self, *args, **kwargs):

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

    self.attrs = attrs

    pd.Series.__init__(self, *args, **kwargs)
    Container.__init__(self, coords=coords)

  def __repr__(self):
    series_str = pd.Series.__repr__(self)
    return (self.metacsv_str + '\n' + series_str + '\n\n' + self.coords_str + self.attr_str)
    
  def to_pandas(self):
    ''' return a copy of the data in a pandas.Series object '''
    return pd.Series(self)



class DataFrame(Container, pd.DataFrame):
  '''
  metacsv.DataFrame, inherrited from pandas.DataFrame
  '''

  _metadata = [
    
    'attrs',        # Metadata/documentation attributes
    '_variables',    # Column Names
    '_coords'       # Coordinates
  ]

  pandas_parent = pd.DataFrame

  @property
  def _constructor(self):
    return DataFrame

  @property
  def _constructor_sliced(self):
    return Series

  @property
  def _constructor_expanddims(self):
    return Panel

  @property
  def variables(self):
    return self._variables

  def __init__(self, *args, **kwargs):

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

    self.attrs = attrs

    pd.DataFrame.__init__(self, *args, **kwargs)
    Container.__init__(self, coords=coords)

    if len(self.index.names) == 1 and (self.index.names[0] is None):
      append=False
    else:
      append=True

    set_coords = [c for c in self.coords if (c not in self.index.names) and (c in self.columns)]
    if len(set_coords) > 0:
      self.set_index(set_coords, append=append, inplace=True)

    self._variables = Variables(variables)

  @property
  def var_str(self):
    return ('Variables\n' + 
      '\n'.join(['    {}'.format(v) for v in self.columns])
      )
    
  def __repr__(self):
    df_str = pd.DataFrame.__repr__(self)
    return (self.metacsv_str + '\n' + df_str + '\n\n' + self.coords_str + '\n' + self.var_str + self.attr_str)

  def to_pandas(self):
    ''' return a copy of the data in a pandas.DataFrame object '''
    return pd.DataFrame(self)


class Panel(pd.Panel):

  _metadata = [
    'attrs',        # Metadata/documentation attributes
    '_coords'       # Coordinates
  ]

  pandas_parent = pd.Panel

  @property
  def _constructor(self):
    return Panel

  @property
  def _constructor_sliced(self):
    return DataFrame

  def __init__(self, *args, **kwargs):

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

    self.attrs = attrs
   
    pd.Series.__init__(self, *args, **kwargs)
    Container.__init__(self, coords=coords)
    
  def __repr__(self):
    panel_str = pd.Panel.__repr__(self)
    return (self.metacsv_str + '\n' + panel_str + '\n\n' + self.coords_str + self.attr_str)

  def to_pandas(self):
    ''' return a copy of the data in a pandas.Panel object '''
    return pd.Panel(self)