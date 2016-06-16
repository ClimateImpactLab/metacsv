'''
Utilities for converting metacsv Containers to other data formats
'''

import pandas as pd, yaml
from collections import OrderedDict

xr = None

def import_xarray():
  global xr
  if xr is None:
    try:
      import xarray as xr
    except ImportError:
      raise ImportError('Cannot send to xarray - xarray library not found. See http://xarray.pydata.org/')


def _get_coords_dataarrays_from_index(container):

  global xr
  if xr is None:
    import_xarray()

  coords = OrderedDict()

  for coord in container.base_coords:
    coords[str(coord)] = container._get_coord_data_from_index(coord).values

  for coord in [k for k in container.coords if k not in container.base_coords]:
    deps = container.coords[coord]
    coords[str(coord)] = xr.DataArray.from_series(pd.Series(container._get_coord_data_from_index(coord), index=pd.MultiIndex.from_tuples(list(zip(*tuple(container._get_coord_data_from_index(dep) for dep in deps))), names=list(map(str, deps)))))

  return coords

def convert_to_xarray(container):
  '''
  Converst metacsv Containers to xarray data types. Requires xarray.
  '''
  
  global xr
  if xr is None:
    import_xarray()

  if container.coords == None:
    container.add_coords()

  if container.coords == None:
    raise ValueError

  if len(container.shape) > 2:
    raise NotImplementedError("to_xarray not yet implemented for Panel data")

  if len(container.shape) == 1:
    coords = _get_coords_dataarrays_from_index(container)
    return xr.DataArray.from_series(pd.Series(
      container.values, 
      index=pd.MultiIndex.from_tuples(
        list(zip(*tuple([container._get_coord_data_from_index(coord) for coord in container.base_coords]))), 
        names=list(map(str, container.base_coords)))))

  if len(container.shape) == 2:

    ds = xr.Dataset()

    for coord in container.base_coords:
      ds.coords[str(coord)] = container.index.get_level_values(coord).unique()


    for coord in container.coords:
      if coord in container.base_coords:
        continue

      ds.coords[str(coord)] = xr.DataArray.from_series(container.stringify_index_names(container.get_unique_multiindex(container.reset_index([c for c in container.index.names if c not in container._coords._base_dependencies[coord]], drop=False, inplace=False)[coord])))

    for col in container.columns:
      reset = [c for c in container.index.names if not c in container.base_coords]
      if len(reset) > 0:
        ds[str(col)] = xr.DataArray.from_series(container.stringify_index_names(container.get_unique_multiindex(container.reset_index(reset, drop=False, inplace=False)[col])))
      else:
        ds[str(col)] = xr.DataArray.from_series(container.stringify_index_names(container.get_unique_multiindex(container[col])))

    ds.attrs.update(container.attrs)

    if hasattr(container, 'variables') and container.variables != None:
      for var, attrs in container.variables.items():
        if var in ds.data_vars:
          ds.data_vars[var].attrs.update(attrs)

        if var in ds.coords:
          ds.coords[var].attrs.update(attrs)

    return ds



def write_to_csv_object(container, fp, *args, **kwargs):
  attr_dict = {}
  attr_dict.update(dict(container.attrs))

  if container.coords is not None:
    attr_dict.update({'coords': dict(container.coords.items())})

  if hasattr(container, 'variables'):
    attr_dict.update({'variables': dict(container.variables.items())})

  fp.write('---\n')
  fp.write(yaml.safe_dump(attr_dict, default_flow_style=False, allow_unicode=True))
  fp.write('---\n')
  container.pandas_parent.to_csv(container, fp, *args, **kwargs)