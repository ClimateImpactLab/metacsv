'''
Utilities for converting between metacsv-compatible data formats
'''

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import pandas as pd
import numpy as np
import xarray as xr
from collections import OrderedDict
from .to_xarray import metacsv_series_to_dataarray, metacsv_series_to_dataset, metacsv_dataframe_to_dataset, metacsv_dataframe_to_dataarray
from .to_csv import metacsv_to_csv, metacsv_to_header, _header_to_file_object
from .parsers import read_csv
from ..core.containers import Series, DataFrame, Panel
from ..core.internals import Coordinates, Variables, Attributes
from .._compat import string_types, stream_types, BytesIO, StringIO


def _coerce_to_metacsv(container, *args, **kwargs):

    if not isinstance(container, (Series, DataFrame, Panel)):
        if isinstance(container, (string_types, stream_types)):
            container = read_csv(container, *args, **kwargs)
        elif isinstance(container, pd.Series):
            container = Series(container)
        elif isinstance(container, pd.DataFrame):
            container = DataFrame(container)
        elif isinstance(container, pd.Panel):
            container = Panel(container)
        elif isinstance(container, (xr.DataArray, xr.Dataset)):
            raise NotImplementedError(
                'automatic coersion of xarray objects not implemented')
        else:
            raise TypeError(
                'Unknown data type. Must be a Series, DataFrame, or Panel')

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
    Convert a CSV, Series, DataFrame, Panel, DataArray, or Dataset to an 
    :py:class:`xarray.Dataset`

    .. note ::

        If a Series is passed, the variable will be named 'data'. to_dataset is 
        not implemented for Panel data.

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

        >>> metacsv.to_dataset(
        ... pd.DataFrame(np.random.rand((3,4))), 
        ... attrs={'author': 'my name'})
        <xarray.Dataset>
        Dimensions:  (index: 3)
        Coordinates:
          * index    (index) int64 0 1 2
        Data variables:
            0        (index) float64 0.0413 0.9774 0.5508
            1        (index) float64 0.7497 0.1899 0.3258
            2        (index) float64 0.6271 0.2384 0.7894
            3        (index) float64 0.252 0.3001 0.02566
        Attributes:
            author: my name

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

        >>> metacsv.to_dataarray(
        ... pd.DataFrame(np.random.rand((3,4))), 
        ... attrs={'author': 'my name'})
        <xarray.DataArray (index: 3, coldim_0: 4)>
        array([[ 0.51152619,  0.34670179,  0.81301656,  0.15533132],
               [ 0.96679786,  0.99511175,  0.46737635,  0.30923316],
               [ 0.21081805,  0.3382857 ,  0.21866735,  0.21965021]])
        Coordinates:
          * index     (index) int64 0 1 2
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

        >>> df = metacsv.DataFrame(
        ... np.random.random((3,4)), columns=['col'+str(i) for i in range(4)])
        >>> df.index = pd.MultiIndex.from_tuples([('a','X'),('b','Y'),('c','Z')], 
        ... names=['abc','xyz'])
        >>> df.attrs={'author': 'my name'}
        >>> df.coords = {'abc': None, 'xyz': ['abc']}
        >>> df
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

        >>> metacsv.to_xarray(df)
        <xarray.Dataset>
        Dimensions:  (abc: 3)
        Coordinates:
          * abc      (abc) object 'a' 'b' 'c'
            xyz      (abc) object 'X' 'Y' 'Z'
        Data variables:
            col0     (abc) float64 0.9078 0.5208 0.8503
            col1     (abc) float64 0.2021 0.8819 0.6013
            col2     (abc) float64 0.01293 0.5816 0.4621
            col3     (abc) float64 0.5058 0.1137 0.1425
        Attributes:
            author: my name
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

        >>> metacsv.to_pandas(df) # doctest: +SKIP
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

        >>> metacsv.to_netcdf(
        ... pd.DataFrame(np.random.rand((3,4))), 
        ... 'test.nc', 
        ... attrs={'author': 'my name'})
        >>> xr.open_dataset('test.nc')
        <xarray.Dataset>
        Dimensions:  (index: 3)
        Coordinates:
          * index    (index) int64 0 1 2
        Data variables:
            0        (index) float64 0.0413 0.9774 0.5508
            1        (index) float64 0.7497 0.1899 0.3258
            2        (index) float64 0.6271 0.2384 0.7894
            3        (index) float64 0.252 0.3001 0.02566
        Attributes:
            author: my name
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
        >>> metacsv.to_csv(
        ...     df,
        ...     fp='my-metacsv-data.csv',
        ...     attrs={'author': 'my name'},
        ...     coords=['alpha', 'beta'])
        ...

    This metacsv-formatted CSV can be then used by metacsv or converted using
    any of the converters in this module:

    ... code-block:: python

        >>> metacsv.to_xarray('my-metacsv-data.csv')
        <xarray.Dataset>
        Dimensions:  (alpha: 2, beta: 2)
        Coordinates:
          * alpha    (alpha) object 'A' 'B'
          * beta     (beta) int64 1 2
        Data variables:
            A        (alpha, beta) float64 0.417 0.1468 0.3968 nan
            B        (alpha, beta) float64 0.7203 0.09234 0.5388 nan
            C        (alpha, beta) float64 0.0001144 0.1863 0.4192 nan
            D        (alpha, beta) float64 0.3023 0.3456 0.6852 nan
        Attributes:
            author: my name

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

        >>> metacsv.to_header('mycsv.header', attrs={'author': 'me'}, coords='index')

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
            

