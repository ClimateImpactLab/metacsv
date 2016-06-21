'''
Utilities for converting metacsv Containers to other data formats
'''

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import pandas as pd, numpy as np
from collections import OrderedDict
from .to_xarray import metacsv_series_to_dataarray, metacsv_series_to_dataset, metacsv_dataframe_to_dataset, metacsv_dataframe_to_dataarray
from .to_csv import metacsv_to_csv
from ..core.containers import Series, DataFrame, Panel
from .._compat import string_types


def _coerce_to_metacsv(container):
  if not isinstance(container, (Series, DataFrame, Panel)):
    if isinstance(container, pd.Series):
      container = Series(container)
      container.add_coords()
    elif isinstance(container, pd.DataFrame):
      container = DataFrame(container)
      container.add_coords()
    elif isinstance(container, pd.Panel):
      container = Panel(container)
      container.add_coords()
    else:
      raise TypeError('Unknown data type. Must be a Series, DataFrame, or Panel')
  return container

def to_dataset(container, attrs=None, coords=None, variables=None):

  container = _coerce_to_metacsv(container)
  
  for name, prop in [('attrs', attrs), ('coords', coords), ('variables', variables)]:
    if prop is not None:
      container.__dict__[name] = prop


  if len(container.shape) == 1:
    return metacsv_series_to_dataset(container)
  elif len(container.shape) == 2:
    return metacsv_dataframe_to_dataset(container)
  elif len(container.shape) > 2:
    raise NotImplementedError('to_dataarray not yet implemented for Panel data')


def to_dataarray(container, attrs=None, coords=None, variables=None):

  container = _coerce_to_metacsv(container)
  
  for name, prop in [('attrs', attrs), ('coords', coords), ('variables', variables)]:
    if prop is not None:
      container.__dict__[name] = prop


  if len(container.shape) == 1:
    return metacsv_series_to_dataarray(container)
  elif len(container.shape) == 2:
    return metacsv_dataframe_to_dataarray(container)
  elif len(container.shape) > 2:
    raise NotImplementedError('to_dataarray not yet implemented for Panel data')

def to_xarray(container, attrs=None, coords=None, variables=None):

  container = _coerce_to_metacsv(container)
  
  for name, prop in [('attrs', attrs), ('coords', coords), ('variables', variables)]:
    if prop is not None:
      container.__dict__[name] = prop

  if len(container.shape) == 1:
    return to_dataarray(container)
  elif len(container.shape) == 2:
    return to_dataset(container)
  elif len(container.shape) > 2:
    raise NotImplementedError('to_dataarray not yet implemented for Panel data')

def to_pandas(container):
  if hasattr(container, 'pandas_parent'):
    return container.pandas_parent(container)


def to_csv(container, fp, attrs=None, coords=None, variables=None, *args, **kwargs):
  
  for name, prop in [('attrs', attrs), ('coords', coords), ('variables', variables)]:
    if prop is not None:
      container = _coerce_to_metacsv(container)
      container.__dict__[name] = prop

  metacsv_to_csv(container, fp, *args, **kwargs)