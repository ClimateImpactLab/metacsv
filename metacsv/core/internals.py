
from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import pandas as pd
import numpy as np
import re
from collections import OrderedDict

try:
    from pandas.core.base import FrozenList
except ImportError:
    FrozenList = list

from .exceptions import GraphIsCyclicError
from .._compat import string_types, has_iterkeys, iterkeys, has_iteritems, iteritems
from ..io import to_xarray, to_csv, to_pandas


class _BaseProperty(object):
    property_type = None  # overload
    repr_order = []

    def __init__(self, data=None, container=None):
        if data is None:
            self._data = None
        elif isinstance(data, _BaseProperty):
            self._data = data._data
        else:
            if isinstance(data, dict) or isinstance(data, OrderedDict):
                self._data = data
            else:
                raise TypeError

    def __repr__(self):
        return str(self)

    def __str__(self):
        truncate = lambda s: '\n'.join([l if len(l) < 80 else l[:75] + '...' for l in s.split('\n')])
        if self._data is not None and len(self._data) > 0:
            repr_str = '' if len(self._data) == 0 else self.property_type
            for props, prop_data in self._data.items():
                repr_str += '\n    {: <15} {}'.format(
                    str(props) + ':', prop_data)
            return truncate(repr_str)
        else:
            return '<Empty {}>'.format(self.property_type)

    def __iter__(self):
        if self._data is not None:
            for k, v in self._data.items():
                yield k, v

    def pop(self, key, *default):
        if len(default) > 1:
            raise ValueError(
                'pop() takes exactly 2 arguments ({} given)'.format(len(default) + 1))

        if self._data is not None:
            if len(default) == 0:
                return self._data.pop(key)
            else:
                return self._data.pop(key, default[0])

        else:
            if len(default) == 1:
                return default[0]

            else:
                raise KeyError(
                    '{} not yet assigned.'.format(self.property_type))

    def get(self, key, *default):
        if len(default) > 1:
            raise ValueError(
                'get() takes exactly 2 arguments ({} given)'.format(len(default) + 1))

        if self._data is not None:
            if len(default) == 0:
                return self._data.get(key)
            else:
                return self._data.get(key, default[0])

        else:
            if len(default) == 1:
                return default[0]

            else:
                raise KeyError(
                    '{} not yet assigned.'.format(self.property_type))

    def update(self, value):
        if self._data == None:
            self._data = {}

        if isinstance(value, _BaseProperty):
            self._data.update(value._data)
        elif has_iterkeys(value):
            if len(value) > 0:
                self._data.update(value)
        else:
            raise TypeError('Passed value is not iterable')

    def __getitem__(self, key):
        if self._data is None:
            raise KeyError('{} not yet assigned.'.format(self.property_type))
        return self._data[key]

    def __setitem__(self, key, value):
        if self._data is None:
            self._data = {}

        if isinstance(value, _BaseProperty):
            self._data[key] = value._data
        else:
            self._data[key] = value

    def __delitem__(self, key):
        if self._data is None:
            raise KeyError('{} not yet assigned.'.format(self.property_type))
        del self._data[key]

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        if '_data' in self.__dict__:
            if self.__dict__['_data'] != None:
                if key in self.__dict__['_data']:
                    return self.__dict__['_data'][key]
        raise AttributeError("'{}' object has no attribute '{}'".format(self.property_type, key))

    def __eq__(self, other):
        if hasattr(other, '_data'):
            return dict(self._data) == dict(other._data)
        if other is None and (self._data is None or len(self._data) == 0):
            return True
        elif has_iteritems(other):
            return dict(self._data) == dict(other)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __contains__(self, key):
        if self._data is None:
            return False
        return key in self._data

    def __len__(self):
        if self._data is None:
            return 0
        return len(self._data)

    def items(self):
        if self._data is not None:
            for k, v in self._data.items():
                yield (k, v)

    def iteritems(self):
      return self.items()

    def copy(self):
        if self._data is not None:
            return type(self)(self._data.copy(), container=None)
        else:
            return type(self)()


class Attributes(_BaseProperty):
    property_type = 'Attributes'


class Variables(_BaseProperty):
    property_type = 'Variables'

    @staticmethod
    def parse_string_var(defn):
        if not isinstance(defn, string_types):
            raise TypeError('parse_string_var only accepts string arguments')
        pattern = re.search(r'^(?P<desc>[^\[]+)(\s+\[(?P<unit>.*)\])?$', defn)
        if not pattern:
            return defn
        vardata = {'description': pattern.group('desc')}
        unit = pattern.group('unit')
        if unit:
            vardata['unit'] = unit
        return vardata

    def __str__(self):
        truncate = lambda s: '\n'.join([l if len(l) < 80 else l[:75] + '...' for l in s.split('\n')])
        if self._data is not None and len(self._data) > 0:
            repr_str = '' if len(self._data) == 0 else self.property_type
            for props, prop_data in self._data.items():
                item_str = '\n    {: <10} {}'.format(
                    str(props) + ':', (prop_data if not has_iteritems(prop_data) else '\n' + '\n'.join([' '*8 + '{: <15} {}'.format(k, v) for k, v in iteritems(prop_data)])))
                repr_str += item_str
            return truncate(repr_str)
        else:
            return '<Empty {}>'.format(self.property_type)


class Coordinates(object):
    '''
    Manages coordinate system for MetaCSV data containers
    '''

    property_type = 'Coordinates'

    def __init__(self, coords=None, container=None):

        if container is not None:
            if not isinstance(container, (Container, pd.DataFrame, pd.Series)):
                raise TypeError(
                    '__init__ container argument must be a metacsv or pandas DataFrame or Series')

        self._container = container

        if hasattr(coords, 'copy'):
            coords = coords.copy()

        self.__set__(coords)

    def __set__(self, coords):
        self._coords = None
        self._base_coords = None
        self._base_dependencies = None

        if isinstance(coords, Coordinates) and (coords._coords is None or (len(coords._coords) == 0)):
            return
        elif coords is None or (len(coords) == 0):
            return
        elif isinstance(coords, Coordinates):
            _coords = coords._coords
            _base_coords = coords._base_coords
            _base_dependencies = coords._base_dependencies
        else:
            _coords, _base_coords, _base_dependencies = self.parse_coords_definition(
                coords)

        self._send_coords_in_cols_to_index(_coords)
        self._validate_coords_against_data(coords=_coords)

        self._coords = _coords
        self._base_coords = _base_coords
        self._base_dependencies = _base_dependencies

    def __repr__(self):
        coords_str = 'Coordinates'
        if self._coords is not None:
            for base in self._base_coords:
                coords_str += '\n' + self._repr_coord(base, base=True)
            for coord in [c for c in self._coords if not c in self._base_coords]:
                coords_str += '\n' + self._repr_coord(coord, base=False)
            return coords_str
        else:
            return '<Empty {}>'.format(self.property_type)

    def __iter__(self):
        if self._coords is not None:
            for k in self._coords.keys():
                yield k

    # TODO:
    # ensure compatability with PY3 and
    # pd._compat utilities
    def items(self):
        if self._coords is not None:
            for k, v in self._coords.items():
                yield (k, v)

    def iteritems(self):
        for k, v in self.items():
            yield k, v

    def __eq__(self, other):
        if isinstance(other, Coordinates):
            return ((dict(self._coords) == dict(other._coords)) and (self._base_coords == other._base_coords))
        elif (other is None) and (self._coords is None):
            return True
        elif has_iteritems(other):
            _coords, _base_coords, _deps = self.parse_coords_definition(other)
            return ((dict(self._coords) == _coords) and (self._base_coords == _base_coords))
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getitem__(self, key):
        if self._coords is None:
            raise KeyError('Coordinate not yet defined')
        return self._coords[key]

    def __len__(self):
        if self._coords is None:
            return 0
        return len(self._coords)

    def __lenth_hint__(self):
        if self._coords is None:
            return 0
        if hasattr(self._coords, '__length_hint__'):
            return self._coords.__lenth_hint__()
        return self.__len__()

    def _repr_coord(self, coord, base=False, maxlen=50):
        if self._container is None:
            datastr = ''
        else:
            datastr = ''
            if isinstance(self._container.index, pd.MultiIndex):
                coord_data = self._container.index.levels[
                    self._container.index.names.index(coord)]
            else:
                coord_data = self._container.index.values

            datastr += ' {} '.format(coord_data.dtype)

            for i, ind in enumerate(coord_data):
                if len(datastr) + len(str(ind)) + 5 > maxlen:
                    datastr += '...'
                    break

                if i > 0:
                    datastr += ', '

                datastr += '{}'.format(ind)

        coordstr = ('  * ' if base else '    ')
        coordstr += ('{: <10}'.format(coord))
        coordstr += (' ({})'.format(coord if base else ','.join(
            list(map(str, self._coords[coord])))))
        coordstr += datastr

        return coordstr

    def copy(self):
        if self._coords is None:
            return type(self)()
        return type(self)(self._coords.copy(), container=None)

    @property
    def base_coords(self):
        return self._base_coords

    @staticmethod
    def parse_coords_definition(coords=None):
        ''' Validate coords to test for cyclic graph '''
        if coords == None:
            return None, None, None

        if isinstance(coords, string_types):
            return OrderedDict([(coords, None)]), FrozenList([coords]), {coords: set([coords])}

        elif not has_iterkeys(coords):
            if isinstance(coords, Coordinates):
                coords = coords._coords
            coords = OrderedDict(
                list(zip(list(coords), [None for _ in range(len(coords))])))
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

        # Convert from sets to lists
        for k, v in dependencies.items():
            if v is not None:
                dependencies[k] = list(v)

        return dependencies, FrozenList(base_coords), base_deps

    def _get_coords_from_data(self):

        if not pd.isnull(self._container.index.names).any():
            coords, base_coords, base_dependencies = self.parse_coords_definition(
                self._container.index.names)

        elif len(self._container.index.names) == 1 and self._container.index.names[0] is None:
            self._container.index.names = ['index']
            coords, base_coords, base_dependencies = self.parse_coords_definition(
                self._container.index.names)

        elif pd.isnull(self._container.index.names).any():
            self._container.index.names = [coord if coord is not None else 'level_{}'.format(
                i) for i, coord in enumerate(self._container.index.names)]
            coords, base_coords, base_dependencies = self.parse_coords_definition(
                self._container.index.names)

        return coords, base_coords, base_dependencies

    def set_coords_from_data(self):
        self._coords, self._base_coords, self._base_dependencies = self._get_coords_from_data()

    def update(self, coords=None):  # This needs some testing!!

        if coords is None:
            coords = self._coords

        if coords is None:
            if self._container is None:
                raise ValueError(
                    'Cannot update coordinates from data unless assigned to a container')

            coords, base_coords, base_dependencies = self._get_coords_from_data()

        self._prune()

        if (not hasattr(self, '_coords')) or self._coords is None:
            _coords = OrderedDict()
        else:
            _coords = self._coords.copy()

        orig_coords = _coords
        for k, v in coords.items():
            orig_coords[k] = v
        self.__set__(orig_coords)

    def _send_coords_in_cols_to_index(self, coords=None, container=None):
        coords = coords if coords is not None else self._coords
        if coords is None:
            return

        container = container if container is not None else self._container

        if self._container is None:
            return

        if hasattr(container, 'columns') and hasattr(container, 'set_index'):
            if len(container.index.names) == 1 and (container.index.names[0] is None):
                append = False
            else:
                append = True

            set_coords = [c for c in coords if (
                c not in container.index.names) and (c in container.columns)]
            if len(set_coords) > 0:
                container.set_index(set_coords, inplace=True, append=append)

    @staticmethod
    def _get_available_coords(container):
        available_coords = []
        for dim in ['index', 'columns']:
            if hasattr(container, dim):
                available_coords.extend(
                    [i for i in container.__getattr__(dim).names if i is not None])

        return available_coords

    def _prune(self, coords=None, container=None):
        coords = coords if coords is not None else self._coords
        if coords is None:
            return

        container = container if container is not None else self._container
        if container is None:
            return

        available_coords = self._get_available_coords(container)
        for c in coords:
            if c not in available_coords:
                coords.pop(c)

        return coords

    def _validate_coords_against_data(self, coords=None, container=None):
        if coords is None:
            return

        container = container if container is not None else self._container
        if container is None:
            return

        for c in coords.keys():
            assert c in container.index.names, "Coordinate '{c}' not found in container index".format(
                c=c)

        for c in container.index.names:
            assert c in coords, "Data index '{c}' not found in supplied coordinates".format(
                c=c)


class Container(object):
    '''
    Base class for metacsv Container objects

    Parameters
    ----------

    coords : dict

        Container coordinates

    variables : dict

        Variable-specific attributes

    attrs : dict

        Container attributes

    Returns
    -------

    container : object

        a :py:class:`~metacsv.Series` or :py:class:`~metacsv.DataFrame` object

    '''

    def __init__(self, coords=None, variables=None, attrs=None, *args, **kwargs):

        self.coords = coords
        self.attrs = attrs
        self.variables = variables

    # Container Properties

    # coords

    @property
    def coords(self):
        '''Coordinates property of a metacsv Container'''
        if not hasattr(self, '_coords'):
            self._coords = Coordinates()

        return self._coords

    @coords.setter
    def coords(self, value):
        if value is None:
            self._coords = Coordinates()
        else:
            self._coords = Coordinates(value, container=self)

    @coords.deleter
    def coords(self):
        self._coords = None

    @property
    def base_coords(self):
        if not hasattr(self, '_coords'):
            self.coords = Coordinates()

        if self.coords == None:
            return None

        return self._coords._base_coords

    # attrs

    @property
    def attrs(self):
        '''Coordinates property of a metacsv Container'''
        if not hasattr(self, '_attrs'):
            self._attrs = Attributes()

        return self._attrs

    @attrs.setter
    def attrs(self, value):
        if value is None:
            self._attrs = Attributes()
        else:
            self._attrs = Attributes(value, container=self)

    @attrs.deleter
    def attrs(self):
        self._attrs = None

    # variables

    @property
    def variables(self):
        '''Coordinates property of a metacsv Container'''
        if not hasattr(self, '_variables'):
            self._variables = Variables()

        return self._variables

    @variables.setter
    def variables(self, value):
        if value is None:
            self._variables = Variables()
        else:
            self._variables = Variables(value, container=self)

    @variables.deleter
    def variables(self):
        self._variables = None

    # Special Container Methods

    def add_coords(self):
        if self.coords == None:
            self.coords = Coordinates(container=self)

        self.coords.set_coords_from_data()

    def _get_coord_data_from_index(self, coord):
        return self.index.get_level_values(coord)

    @staticmethod
    def get_unique_multiindex(series):
        return series.iloc[np.unique(series.index.values, return_index=True)[1]]

    @staticmethod
    def stringify_index_names(series):
        series.index.names = list(map(str, series.index.names))
        return series

    @staticmethod
    def strip_special_attributes(args, kwargs):

        attrs = kwargs.pop('attrs', {}).copy()

        def update_property(p_data, data, func=lambda x: x):
            if hasattr(data, 'copy'):
                data = data.copy()
            parsed = func(data)
            if parsed != None:
                p_data.update(parsed)

        def strip_property(prop, func=lambda x: x):
            p_data = {}

            update_property(p_data, attrs.pop(prop, {}), func)
            update_property(p_data, kwargs.pop(prop, {}), func)

            if len(p_data) == 0:
                p_data = None

            return p_data

        coords = strip_property(
            'coords', lambda x: Coordinates.parse_coords_definition(x)[0])
        variables = strip_property('variables')

        special = {}

        if (coords is not None) and (len(coords) > 0):
            special['coords'] = coords

        if (variables is not None) and (len(variables) > 0):
            special['variables'] = variables

        if (attrs is not None) and (len(attrs) > 0):
            special['attrs'] = attrs

        return args, kwargs, special


    # Container formatting

    def _print_format(self):
        metacsv_str = '<{} {}>'.format(
            type(self).__module__ + '.' + type(self).__name__, self.shape)
        data_str = self.pandas_parent.__str__(self.to_pandas())
        postscript = '\n'.join(
            [str(p) for p in [self.coords, self.variables, self.attrs] if p != None])
        return (metacsv_str + '\n' + data_str + ('\n\n' if len(postscript) > 0 else '') + postscript)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self._print_format()

    # Container conversion & I/O

    def to_csv(self, fp, header_file=None, *args, **kwargs):
        '''
        Write to a metacsv-formatted csv

        Parameters
        ----------

        fp : str

            Path to which to write the metacsv-formatted CSV

        header_file : str_or_buffer

            A separate metacsv-formatted header file

        *args :

            passed to pandas.to_csv

        **kwargs :

            passed to pandas.to_csv

        Example
        -------

        .. code-block:: python

            >>> from metacsv import DataFrame
            >>> import numpy as np
            >>> np.random.seed(1)
            >>>
            >>> DataFrame(
            ...     pd.DataFrame(np.random.random((3,4))),
            ...     attrs={'author': 'my name'}
            ...     ).to_csv('my-metacsv-data.csv')

            >>> import os
            >>> os.remove('my-metacsv-data.csv')

        '''
        to_csv.metacsv_to_csv(self, fp, header_file=None, *args, **kwargs)

    def to_header(self, fp):
        '''
        Write attributes directly to a metacsv-formatted header file

        fp : str

            Path to which to write the metacsv-formatted header file

        Example
        -------

        .. code-block:: python

            >>> from metacsv import DataFrame
            >>> import numpy as np
            >>> np.random.seed(1)
            >>>
            >>> df = DataFrame(
            ...     np.random.random((3,4)),
            ...     columns=['col'+str(i) for i in range(4)])
            ...
            >>> df.attrs={'author': 'my name'}
            >>> df.to_header('mycsv.header')

            >>> import os
            >>> os.remove('mycsv.header')
        '''

        to_csv.metacsv_to_header(fp, attrs=self.attrs, coords=self.coords, variables=self.variables)

    def to_pandas(self):
        '''
        Strip metacsv special attributes and return pandas Series or DataFrame

        Example
        -------

        .. code-block:: python

            >>> from metacsv import DataFrame
            >>> import numpy as np, pandas as pd
            >>> np.random.seed(1)
            >>>
            >>> df = DataFrame(
            ...     np.random.random((3,4)),
            ...     columns=['col'+str(i) for i in range(4)])
            ...
            >>> df.index = pd.MultiIndex.from_tuples(
            ...     [('a','X'),('b','Y'),('c','Z')],
            ...     names=['abc','xyz'])
            ...
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

            >>> df.to_pandas() # doctest: +NORMALIZE_WHITESPACE
                         col0      col1      col2      col3
            abc xyz
            a   X    0.417022  0.720324  0.000114  0.302333
            b   Y    0.146756  0.092339  0.186260  0.345561
            c   Z    0.396767  0.538817  0.419195  0.685220

        '''

        return self.pandas_parent(self)

    def to_xarray(self):
        '''
        Convert to an xArray.Dataset

        .. note ::

            to_dataset is not yet implemented for Panel data.

        Example
        -------

        .. code-block:: python

            >>> from metacsv import DataFrame
            >>> import numpy as np
            >>> np.random.seed(1)
            >>>
            >>> df = DataFrame(np.random.random((3,4)), columns=['col'+str(i) for i in range(4)])
            >>> df.index = pd.MultiIndex.from_tuples(
            ...     list(zip(str('abc'), str('XYZ'))), names=['abc','xyz'])
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

            >>> df.to_xarray()  # doctest: +NORMALIZE_WHITESPACE
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

        if len(self.shape) == 1:
            return to_xarray.metacsv_series_to_dataarray(self)
        elif len(self.shape) == 2:
            return to_xarray.metacsv_dataframe_to_dataset(self)
        elif len(self.shape) > 2:
            raise NotImplementedError(
                'to_dataarray not yet implemented for Panel data')

    def to_dataarray(self):
        '''
        Convert to an xArray.DataArray

        .. note ::

            If a DataFrame is passed, columns will be stacked and treated as
            coordinates. ``to_dataset`` is not yet implemented for Panel data.

        Example
        -------

        .. code-block:: python

            >>> from metacsv import DataFrame
            >>> import numpy as np
            >>> np.random.seed(1)
            >>>
            >>> df = DataFrame(
            ...     np.random.random((3,4)),
            ...     index=list(str('ABC')),
            ...     attrs={'author': 'my name'})
            ...
            >>> df.to_dataarray() # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
            <xarray.DataArray (ind_0: 3, coldim_0: 4)>
            array([[4.170..., 7.20..., 1.14..., 3.02...],
                   [1.467..., 9.23..., 1.86..., 3.45...],
                   [3.967..., 5.38..., 4.19..., 6.85...]])
            Coordinates:
              * ind_0     (ind_0) object 'A' 'B' 'C'
              * coldim_0  (coldim_0) int64 0 1 2 3
            Attributes:
                author:   my name

        '''
        if len(self.shape) == 1:
            return to_xarray.metacsv_series_to_dataarray(self)
        elif len(self.shape) == 2:
            return to_xarray.metacsv_dataframe_to_dataarray(self)
        elif len(self.shape) > 2:
            raise NotImplementedError(
                'to_dataarray not yet implemented for Panel data')

    def to_dataset(self):
        '''
        Convert to an xArray.Dataset

        .. note ::

            If a Series is passed, the variable will be named 'data'.
            ``to_netcdf`` is not yet implemented for Panel data.

        Example
        -------

        .. code-block:: python

            >>> from metacsv import DataFrame
            >>> import numpy as np
            >>> np.random.seed(1)
            >>>
            >>> df = DataFrame(
            ...     np.random.random((3,4)),
            ...     attrs={'author': 'my name'})
            ...
            >>> df.to_dataset() # doctest: +NORMALIZE_WHITESPACE
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
        if len(self.shape) == 1:
            return to_xarray.metacsv_series_to_dataset(self)
        elif len(self.shape) == 2:
            return to_xarray.metacsv_dataframe_to_dataset(self)
        elif len(self.shape) > 2:
            raise NotImplementedError(
                'to_dataarray not yet implemented for Panel data')

    def to_netcdf(self, fp):
        '''
        Convert to a NetCDF file

        .. note ::

            If a Series is passed, the variable will be named 'data'.

        Parameters
        ----------

        fp : string_or_buffer

            The filepath or file object to be written

        Example
        -------

        .. code-block:: python

            >>> from metacsv import DataFrame
            >>> import numpy as np
            >>> np.random.seed(1)
            >>>
            >>> df = DataFrame(
            ...     np.random.random((3,4)),
            ...     columns=list(str('ABCD')),
            ...     attrs={'author': 'my name'})
            ...
            >>> df.to_netcdf('test.nc')

        .. code-block:: python

            >>> import xarray as xr
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

        self.to_dataset().to_netcdf(fp)
