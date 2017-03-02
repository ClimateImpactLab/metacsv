'''
Utilities for converting metacsv Containers to xarray containers
'''

import pandas as pd
import numpy as np
from collections import OrderedDict
from .._compat import string_types
from .yaml_tools import ordered_dump

xr = None


def _import_xarray():
    global xr
    if xr is None:
        import xarray as xr


def _check_series_unique(series):
    def check_unique(group):
        try:
            name = group.name if isinstance(group.name, string_types) else ','.join(group.name)
        except TypeError:
            name = group.name

        msg = "Data not uniquely indexed for base coords: ({})".format(name)

        if len(group.drop_duplicates()) != 1:
            raise ValueError(msg)

    if len(series.index.names) > 1:
        series.groupby(level=series.index.names).apply(check_unique)
    else:
        series.groupby(by=series.index).apply(check_unique)


def _append_coords_to_dataset(ds, container, base_only, attrs=None):

    global xr
    if xr is None:
        _import_xarray()

    if container.coords == None:
        container.add_coords()

    for coord in container.base_coords:
        ds.coords[str(coord)] = container.index.get_level_values(
            coord).unique()
        ds.coords[str(coord)].attrs = container.variables.get(coord, {})

    for coord in container.coords:
        if coord in container.base_coords:
            continue

        data = base_only[coord]
        if len(data.index.names) > len(container.coords._base_dependencies[coord]):
            data.reset_index([c for c in data.index.names if c not in container.coords._base_dependencies[
                             coord]], inplace=True, drop=True)
        ds.coords[str(coord)] = metacsv_series_to_dataarray(
            data, attrs=container.variables.get(coord, {}))


def metacsv_series_to_dataarray(series, attrs=None):

    global xr
    if xr is None:
        _import_xarray()

    if attrs is None:
        attrs = series.attrs

    if series.base_coords != None:
        reset = [c for c in series.index.names if c not in series.base_coords]

        if len(reset) > 0:
            series = series.reset_index(reset, drop=True)

    _check_series_unique(series)
    series = series.iloc[np.unique(series.index.values, return_index=True)[1]]

    series.index.names = list(map(str, series.index.names))
    da = xr.DataArray.from_series(series)
    da.attrs = attrs

    return da


def metacsv_series_to_dataset(series, name='data', attrs=None):

    global xr
    if xr is None:
        _import_xarray()

    ds = xr.Dataset()

    if attrs is None:
        attrs = series.attrs

    reset = [c for c in series.coords if c not in series.base_coords]

    if len(reset) > 0:
        base_only = series.reset_index(reset, drop=False)
    else:
        base_only = series

    _check_series_unique(base_only)

    _append_coords_to_dataset(ds, series, base_only, attrs)

    if len(reset) > 0:
        data = series.reset_index(reset, drop=True)
    else:
        data = series

    ds[name] = xr.DataArray.from_series(data)
    ds[name].attrs = series.variables.get(name, {})
    ds.attrs = series.attrs

    return ds


def metacsv_dataframe_to_dataset(dataframe, name='data', attrs=None):

    global xr
    if xr is None:
        _import_xarray()

    ds = xr.Dataset()

    if attrs is None:
        attrs = dataframe.attrs

    reset = [c for c in dataframe.coords if c not in dataframe.base_coords]

    if len(reset) > 0:
        base_only = dataframe.reset_index(reset, drop=False, inplace=False)
    else:
        base_only = dataframe

    _check_series_unique(base_only)

    _append_coords_to_dataset(ds, dataframe, base_only, attrs)

    if len(reset) > 0:
        data = dataframe.reset_index(reset, drop=True)
    else:
        data = dataframe

    for col in dataframe.columns:
        ds[col] = xr.DataArray.from_series(data[col])
        ds[col].attrs = dataframe.variables.get(col, {})
        ds.attrs = dataframe.attrs

    return ds


def metacsv_dataframe_to_dataarray(dataframe, names=None, attrs=None):

    global xr
    if xr is None:
        _import_xarray()

    dataframe = dataframe.copy()

    if attrs is None:
        attrs = dataframe.attrs

    coords = dataframe.coords.copy()

    dataframe.index.names = [
        str(ind) if not pd.isnull(ind) else 'ind_{}'.format(i)
            for i, ind in enumerate(dataframe.index.names)]

    if dataframe.coords == None:
        coords.update({c: None for c in dataframe.index.names})

    dataframe.columns.names = [
        str(c) if not pd.isnull(c) else 'coldim_{}'.format(i)
            for i, c in enumerate(dataframe.columns.names)]

    colnames = dataframe.columns.names
    series = dataframe._constructor_sliced(dataframe.stack(colnames))
    coords.update({c: None for c in colnames})

    series.coords.update(coords)
    return metacsv_series_to_dataarray(series, attrs=attrs)
