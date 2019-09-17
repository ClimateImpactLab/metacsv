from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import pandas as pd
import numpy as np
import yaml
import warnings
from .._compat import string_types

from .internals import Attributes, Container, Coordinates, Variables
import xarray as xr

class Series(Container, pd.Series):
    '''
    metacsv.Series, inherrited from pandas.Series

    Keyword Arguments:
        attrs     : dict-like
            Attributes of this container
        coords    : list or dict-like
            Coordinate dependencies
        variables :  dict-like
            Variable-specific attributes

    *args, **kwargs are passed to pandas.Series.__init__
    '''

    pandas_parent = pd.Series
    _metadata = ['_coords', '_attrs', '_variables']

    def copy(self):
        return Series(
            self.pandas_parent.copy(self),
            coords=self.coords.copy(),
            attrs=self.attrs.copy(),
            variables=self.variables.copy())

    @property
    def _constructor(self):
        return Series

    @property
    def _constructor_expanddim(self):
        return DataFrame

    def __init__(self, *args, **kwargs):
        args, kwargs, special = Container.strip_special_attributes(
            args, kwargs)
        pd.Series.__init__(self, *args, **kwargs)
        Container.__init__(self, **special)


class DataFrame(Container, pd.DataFrame):
    '''
    metacsv.DataFrame, inherrited from pandas.DataFrame

    Keyword Arguments:
        attrs     : dict-like
            Attributes of this container
        coords    : list or dict-like
            Coordinate dependencies
        variables :  dict-like
            Variable-specific attributes

    *args, **kwargs are passed to pandas.DataFrame.__init__
    '''

    pandas_parent = pd.DataFrame
    _metadata = ['_coords', '_attrs', '_variables']

    def copy(self):
        return DataFrame(
            self.pandas_parent.copy(self),
            coords=self.coords.copy(),
            attrs=self.attrs.copy(),
            variables=self.variables.copy())

    @property
    def _constructor(self):
        return DataFrame

    @property
    def _constructor_sliced(self):
        return Series

    def __init__(self, *args, **kwargs):
        args, kwargs, special = Container.strip_special_attributes(
            args, kwargs)
        pd.DataFrame.__init__(self, *args, **kwargs)
        Container.__init__(self, **special)
