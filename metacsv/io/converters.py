'''
Utilities for converting between metacsv-compatible data formats
'''

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import pandas as pd
import numpy as np
import xarray as xr
from collections import OrderedDict

from metacsv.io.to_xarray import (
    metacsv_series_to_dataarray,
    metacsv_series_to_dataset,
    metacsv_dataframe_to_dataset,
    metacsv_dataframe_to_dataarray)

from metacsv.io.to_csv import (
    metacsv_to_csv,
    metacsv_to_header,
    _header_to_file_object)

from metacsv.io.parsers import read_csv
from metacsv.core.containers import Series, DataFrame
from metacsv.core.internals import Coordinates, Variables, Attributes
from metacsv._compat import string_types, stream_types, BytesIO, StringIO


def _coerce_to_metacsv(container, *args, **kwargs):

    if not isinstance(container, (Series, DataFrame)):
        if isinstance(container, (string_types, stream_types)):
            container = read_csv(container, *args, **kwargs)
        elif isinstance(container, pd.Series):
            container = Series(container)
        elif isinstance(container, pd.DataFrame):
            container = DataFrame(container)
        elif isinstance(container, (xr.DataArray, xr.Dataset)):
            raise NotImplementedError(
                'automatic coersion of xarray objects not implemented')
        else:
            raise TypeError(
                'Unknown data type. Must be a Series or DataFrame')

    return container


def _parse_args(container, attrs, coords, variables):

    if attrs is not None:
        if hasattr(container, 'attrs') and container.attrs == None:
            container.attrs = attrs
        else:
            container.attrs.update(attrs)

    if coords is not None:
        if hasattr(container, 'coords') and container.coords == None:
            container.add_coords()
            container.coords = coords
        else:
            container.coords.update(coords)

    if variables is not None:
        if hasattr(container, 'variables') and container.variables == None:
            container.variables = variables
        else:
            container.variables.update(variables)


def to_dataset(container, attrs=None, coords=None, variables=None, *args, **kwargs):
    '''
    Convert a CSV, Series or DataFrame, DataArray, or Dataset to an
    :py:class:`xarray.Dataset`

    .. note ::

        If a Series is passed, the variable will be named
        '__xarray_data_variable__'

    Parameters
    ----------

    container : object

        A pandas or metacsv Series, DataFrame, o, an xarray DataArray or
        Dataset, or a filepath to a csv or netcdf file.

    attrs : dict

        Container attributes

    coords : dict

        Container coordinates

    variables : dict

        Variable-specific attributes

    *args :

        Additional positional arguments passed to metacsv.read_csv
        if container is a filepath

    **kwargs :

        Additional keyword arguments passed to metacsv.read_csv
        if container is a filepath

    Example
    -------

    .. code-block:: python

        >>> np.random.seed(1)
        >>>
        >>> to_dataset(
        ...     pd.DataFrame(np.random.random((3,4))),
        ...     attrs={'author': 'my name'}) # doctest: +NORMALIZE_WHITESPACE
        ...
        <xarray.Dataset>
        Dimensions:  (index: 3)
        Coordinates:
          * index    (index) int64 0 1 2
        Data variables:
            0        (index) float64 0.417 0.1468 0.3968
            1        (index) float64 0.7203 0.09234 0.5388
            2        (index) float64 0.0001144 0.1863 0.4192
            3        (index) float64 0.3023 0.3456 0.6852
        Attributes:
            author:  my name

    '''

    container = _coerce_to_metacsv(container, *args, **kwargs)
    _parse_args(container, attrs, coords, variables)

    if len(container.shape) == 1:
        return metacsv_series_to_dataset(container)
    elif len(container.shape) == 2:
        return metacsv_dataframe_to_dataset(container)
    elif len(container.shape) > 2:
        raise NotImplementedError(
            'to_dataarray not implemented for Panel data')


def to_dataarray(container, attrs=None, coords=None, variables=None, *args, **kwargs):
    '''
    Convert a CSV, Series, DataFrame, Panel, DataArray, or Dataset to an
    :py:class:`xarray.DataArray`

    .. note ::

        If a DataFrame is passed, columns will be stacked and treated as
        coordinates. to_dataset is not implemented for Panel data.

    Parameters
    ----------

    container : object

        A pandas or metacsv Series, DataFrame, or Panel, an xarray DataArray or
        Dataset, or a filepath to a csv or netcdf file.

    attrs : dict

        Container attributes

    coords : dict

        Container coordinates

    variables : dict

        Variable-specific attributes

    *args :

        Additional positional arguments passed to metacsv.read_csv
        if container is a filepath

    **kwargs :

        Additional keyword arguments passed to metacsv.read_csv
        if container is a filepath

    Example
    -------

    .. code-block:: python

        >>> np.random.seed(1)
        >>> to_dataarray(
        ...     pd.DataFrame(np.random.random((3,4)), index=list('ABC')),
        ...     attrs={'author': 'my name'})  # doctest: +SKIP
        ...
        <xarray.DataArray (ind_0: 3, coldim_0: 4)>
        array([[4.17022005e-01, 7.20324493e-01, 1.14374817e-04, 3.02332573e-01],
               [1.46755891e-01, 9.23385948e-02, 1.86260211e-01, 3.45560727e-01],
               [3.96767474e-01, 5.38816734e-01, 4.19194514e-01, 6.85219500e-01]])
        Coordinates:
          * ind_0     (ind_0) object 'A' 'B' 'C'
          * coldim_0  (coldim_0) int64 0 1 2 3
        Attributes:
            author: my name

    '''

    container = _coerce_to_metacsv(container, *args, **kwargs)
    _parse_args(container, attrs, coords, variables)

    if len(container.shape) == 1:
        return metacsv_series_to_dataarray(container)
    elif len(container.shape) == 2:
        return metacsv_dataframe_to_dataarray(container)
    elif len(container.shape) > 2:
        raise NotImplementedError(
            'to_dataarray not implemented for Panel data')


def to_xarray(container, attrs=None, coords=None, variables=None, *args, **kwargs):
    '''
    Convert a Series to an xarray.DataArray and a CSV or DataFrame to an xArray.Dataset

    .. note ::

        If a DataFrame is passed, columns will be stacked and treated as
        coordinates. to_dataset is not implemented for Panel data.

    Parameters
    ----------

    container : object

        A pandas or metacsv Series, DataFrame, or Panel, an xarray DataArray or
        Dataset, or a filepath to a csv or netcdf file.

    attrs : dict

        Container attributes

    coords : dict

        Container coordinates

    variables : dict

        Variable-specific attributes

    *args :

        Additional positional arguments passed to metacsv.read_csv
        if container is a filepath

    **kwargs :

        Additional keyword arguments passed to metacsv.read_csv
        if container is a filepath

    Example
    -------

    .. code-block:: python

        >>> import metacsv
        >>> import numpy as np, pandas as pd
        >>>
        >>> np.random.seed(1)
        >>>
        >>> df = metacsv.DataFrame(
        ... np.random.random((3,4)), columns=['col'+str(i) for i in range(4)])
        >>> df.index = pd.MultiIndex.from_tuples([('a','X'),('b','Y'),('c','Z')],
        ... names=['abc','xyz'])
        >>> df.attrs={'author': 'my name'}
        >>> df.coords = {'abc': None, 'xyz': ['abc']}
        >>> df # doctest: +NORMALIZE_WHITESPACE
        <metacsv.core.containers.DataFrame (3, 4)>
                     col0      col1      col2      col3
        abc xyz
        a   X    0.417022  0.720324  0.000114  0.302333
        b   Y    0.146756  0.092339  0.186260  0.345561
        c   Z    0.396767  0.538817  0.419195  0.685220
        <BLANKLINE>
        Coordinates
          * abc        (abc) object a, b, c
            xyz        (abc) object X, Y, Z
        Attributes
            author:    my name

        >>> to_xarray(df) # doctest: +SKIP
        <xarray.Dataset>
        Dimensions:  (abc: 3)
        Coordinates:
          * abc      (abc) object 'a' 'b' 'c'
            xyz      (abc) object 'X' 'Y' 'Z'
        Data variables:
            col0     (abc) float64 0.417 0.1468 0.3968
            col1     (abc) float64 0.7203 0.09234 0.5388
            col2     (abc) float64 0.0001144 0.1863 0.4192
            col3     (abc) float64 0.3023 0.3456 0.6852
        Attributes:
            author:  my name
    '''

    container = _coerce_to_metacsv(container, *args, **kwargs)
    _parse_args(container, attrs, coords, variables)

    if len(container.shape) == 1:
        return to_dataarray(container)
    elif len(container.shape) == 2:
        return to_dataset(container)
    elif len(container.shape) > 2:
        raise NotImplementedError(
            'to_dataarray not implemented for Panel data')


def to_pandas(container, *args, **kwargs):
    '''
    Write a metacsvobject to a pandas :py:class:`~pandas.Series`,
    :py:class:`~pandas.DataFrame`, or :py:class:`~pandas.Panel`

    Parameters
    ----------

    container : object

        A pandas or metacsv Series, DataFrame, or Panel, an xarray DataArray or
        Dataset, or a filepath to a csv or netcdf file.

    *args :

        Additional positional arguments passed to metacsv.to_csv

    **kwargs :

        Additional keyword arguments passed to metacsv.to_csv

    Example
    -------

    .. code-block:: python


        >>> import metacsv
        >>> import numpy as np, pandas as pd
        >>>
        >>> np.random.seed(1)
        >>>
        >>> df = metacsv.DataFrame(
        ...     np.random.random((3,4)),
        ...     columns=['col'+str(i) for i in range(4)])
        ...
        >>> df.index = pd.MultiIndex.from_tuples(
        ...     [('a','X'),('b','Y'),('c','Z')], names=['abc','xyz'])
        ...
        >>> df.attrs={'author': 'my name'}
        >>> df.coords = {'abc': None, 'xyz': ['abc']}
        >>> df # doctest: +SKIP
        <metacsv.core.containers.DataFrame (3, 4)>
                     col0      col1      col2      col3
        abc xyz
        a   X    0.328389  0.598790  0.299902  0.265052
        b   Y    0.720712  0.617109  0.331346  0.558522
        c   Z    0.954494  0.143843  0.058968  0.069010

        Coordinates
          * abc        (abc) object a, b, c
            xyz        (abc) object X, Y, Z
        Attributes
            author:    my name

        >>> to_pandas(df) # doctest: +SKIP
                     col0      col1      col2      col3
        abc xyz
        a   X    0.328389  0.598790  0.299902  0.265052
        b   Y    0.720712  0.617109  0.331346  0.558522
        c   Z    0.954494  0.143843  0.058968  0.069010
        '''

    if not hasattr(container, 'pandas_parent'):
        container = _coerce_to_metacsv(container, *args, **kwargs)

    return container.pandas_parent(container)


def to_netcdf(container, fp, attrs=None, coords=None, variables=None, *args, **kwargs):
    '''
    Convert a CSV, Series, DataFrame, Panel, DataArray, or Dataset to a NetCDF file

    .. note ::

        If a DataFrame is passed, columns will be stacked and treated as
        coordinates. to_dataset is not implemented for Panel data.

    Parameters
    ----------

    container : object

        A pandas or metacsv Series, DataFrame, or Panel, an xarray DataArray or
        Dataset, or a filepath to a csv or netcdf file.

    attrs : dict

        Container attributes

    coords : dict

        Container coordinates

    variables : dict

        Variable-specific attributes

    *args :

        Additional positional arguments passed to metacsv.read_csv
        if container is a filepath

    **kwargs :

        Additional keyword arguments passed to metacsv.read_csv
        if container is a filepath

    Example
    -------

    .. code-block:: python

        >>> np.random.seed(1)
        >>>
        >>> to_netcdf(
        ...     pd.DataFrame(np.random.random((3,4)), columns=list('ABCD')),
        ...     'test.nc',
        ...     attrs={'author': 'my name'})
        ...
        >>> ds = xr.open_dataset('test.nc')
        >>> ds # doctest: +NORMALIZE_WHITESPACE
        <xarray.Dataset>
        Dimensions:  (index: 3)
        Coordinates:
          * index    (index) int64 0 1 2
        Data variables:
            A        (index) float64 ...
            B        (index) float64 ...
            C        (index) float64 ...
            D        (index) float64 ...
        Attributes:
            author:  my name

        >>> ds.close()
        >>> import os
        >>> os.remove('test.nc')
    '''

    to_dataset(container, attrs=attrs, coords=coords, variables=variables, *args, **kwargs).to_netcdf(fp)


def to_csv(container, fp, attrs=None, coords=None, variables=None, header_file=None, *args, **kwargs):
    r'''
    Write a CSV, Series, DataFrame, Panel, DataArray, or Dataset to a metacsv-formatted csv

    .. note ::

        If a DataFrame is passed, columns will be stacked and treated as
        coordinates. to_dataset is not implemented for Panel data.

    Parameters
    ----------

    container : object

        A pandas or metacsv Series, DataFrame, or Panel, an xarray DataArray or
        Dataset, or a filepath to a csv or netcdf file.

    fp : str

        Path to which to write the metacsv-formatted CSV

    attrs : dict

        Container attributes

    coords : dict

        Container coordinates

    variables : dict

        Variable-specific attributes

    header_file : str_or_buffer

        A separate metacsv-formatted header file

    *args :

        Additional positional arguments passed to metacsv.read_csv
        if container is a filepath

    **kwargs :

        Additional keyword arguments passed to metacsv.read_csv
        if container is a filepath

    Example
    -------

    .. code-block:: python

        >>> np.random.seed(1)
        >>> index = pd.MultiIndex.from_tuples(
        ...     [('X', 1), ('X', 2), ('Y', 1)],
        ...     names=['alpha', 'beta'])
        ...
        >>> df = pd.DataFrame(
        ...     np.random.random((3,4)),
        ...     index=index,
        ...     columns=list('ABCD'))
        ...
        >>> to_csv(
        ...     df,
        ...     fp='my-metacsv-data.csv',
        ...     attrs={'author': 'my name'},
        ...     coords=['alpha', 'beta'])
        ...

    This metacsv-formatted CSV can be then used by metacsv or converted using
    any of the converters in this module:

    ... code-block:: python

        >>> to_xarray('my-metacsv-data.csv').transpose(
        ...     'alpha', 'beta') # doctest: +SKIP
        <xarray.Dataset>
        Dimensions:  (alpha: 2, beta: 2)
        Coordinates: ...
          * alpha    (alpha) object 'X' 'Y' ...
        Data variables:
            A        (alpha, beta) float64 0.417 0.1468 0.3968 nan
            B        (alpha, beta) float64 0.7203 0.09234 0.5388 nan
            C        (alpha, beta) float64 0.0001144 0.1863 0.4192 nan
            D        (alpha, beta) float64 0.3023 0.3456 0.6852 nan
        Attributes:
            author:   my name

        >>> import os
        >>> os.remove('my-metacsv-data.csv')

    '''

    container = _coerce_to_metacsv(container, header_file=header_file).copy()
    _parse_args(container, attrs, coords, variables)
    metacsv_to_csv(container, fp, *args, **kwargs)


def to_header(fp, container=None, attrs=None, coords=None, variables=None, *args, **kwargs):
    '''
    Write metacsv attributes directly to a metacsv-formatted header file

    Parameters
    ----------

    fp : str

        Path to which to write the metacsv-formatted header file

    container : object

        A metacsv Series, DataFrame, or Panel, or a metacsv-formatted csv file
        from which to derive attrs, coords, and variables (optional)

    attrs : dict

        Attributes to write to header file (optional). If container is also
        supplied, these attrs will update the attrs dict on the provided
        container.

    coords : dict

        Coordinates to write to header file (optional). If container is also
        supplied, these coords will update the coords dict on the provided
        container.

    variables : dict

        Variable metadata to write to header file (optional). If container is
        also supplied, these variable metadata will update the variables dict
        on the provided container.

    *args :

        Additional positional arguments passed to metacsv.read_csv
        if container is a filepath

    **kwargs :

        Additional keyword arguments passed to metacsv.read_csv
        if container is a filepath

    Example
    -------

    .. code-block:: python

        >>> to_header('mycsv.header', attrs={'author': 'me'}, coords='index')

        >>> import os
        >>> os.remove('mycsv.header')

    '''

    if container is not None:
        container = _coerce_to_metacsv(container, *args, **kwargs).copy()
        _parse_args(container, attrs, coords, variables)
        attrs = container.attrs
        coords = container.coords
        variables = container.variables

    else:
        if not isinstance(attrs, Attributes):
            attrs = Attributes(attrs)

        if not isinstance(coords, Coordinates):
            coords = Coordinates(coords)

        if not isinstance(variables, Variables):
            variables = Variables(variables)

    metacsv_to_header(fp, attrs=attrs, coords=coords, variables=variables)
