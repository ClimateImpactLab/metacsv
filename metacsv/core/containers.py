

import pandas as pd, numpy as np, xarray as xr, yaml
from .._compat import string_types
from collections import OrderedDict
from pandas.core.base import FrozenList

from metacsv.core.internals import Attributes, Container, Coordinates, Variables



class Series(Container, pd.Series):
  '''
  metacsv.Series, inherrited from pandas.Series
  '''

  pandas_parent = pd.Series

  @property
  def _constructor(self):
    return Series

  @property
  def _constructor_expanddim(self):
    return DataFrame

  def __init__(self, *args, **kwargs):
    args, kwargs, special = Container.strip_special_attributes(args, kwargs)
    pd.Series.__init__(self, *args, **kwargs)
    Container.__init__(self, **special)


class DataFrame(Container, pd.DataFrame):
  '''
  metacsv.DataFrame, inherrited from pandas.DataFrame
  '''

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

  def __init__(self, *args, **kwargs):
    args, kwargs, special = Container.strip_special_attributes(args, kwargs)
    pd.DataFrame.__init__(self, *args, **kwargs)
    Container.__init__(self, **special)


class Panel(pd.Panel):
  '''
  metacsv.Panel, inherrited from pandas.Panel
  '''

  pandas_parent = pd.Panel

  @property
  def _constructor(self):
    return Panel

  @property
  def _constructor_sliced(self):
    return DataFrame

  def __init__(self, *args, **kwargs):
    args, kwargs, special = Container.strip_special_attributes(args, kwargs)
    pd.Series.__init__(self, *args, **kwargs)
    Container.__init__(self, **special)
    
