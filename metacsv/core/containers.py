

import pandas as pd, numpy as np, xarray as xr, yaml
from .._compat import string_types
from collections import OrderedDict
from pandas.core.base import FrozenList

from metacsv.core.internals import Attributes, Container, Coordinates, Variables



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

    self._variables = Variables(variables)

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
    

  def to_pandas(self):
    ''' return a copy of the data in a pandas.Panel object '''
    return pd.Panel(self)