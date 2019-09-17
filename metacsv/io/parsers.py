
from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import pandas as pd
import re
from collections import OrderedDict
from .yaml_tools import ordered_load
from .._compat import string_types, has_iteritems, iteritems
from ..core.internals import Container, Attributes, Variables, Coordinates
from ..core.containers import Series, DataFrame


def find_yaml_start(line):
    return re.search(r'^\s*-{3,}\s*$', line) is not None


def find_yaml_stop(line):
    return re.search(r'^\s*\.{3,}\s*$', line) is not None


def _parse_headered_data(fp):

    # Check for a yaml parse break at the top of the file
    # if there is not one, go back to the top and read like a
    # normal CSV
    loc = fp.tell()

    nextline = ''

    while re.search(r'^[\s\n\r]*$', nextline):
        nextline = next(fp)

    if not find_yaml_start(nextline):
        fp.seek(loc)
        return OrderedDict()

    yaml_text = ''
    this_line = ''

    while not find_yaml_stop(this_line):
        yaml_text += '\n' + this_line.rstrip('\n')
        this_line = next(fp)
    yaml_text = yaml_text.replace('\t', ' ')

    header = ordered_load(yaml_text)


    return header

def _verify_deep_assertion(verify_par, par):
    if par is None:
        raise ValueError('Assertions failed')

    if not has_iteritems(verify_par):
        if hasattr(verify_par, '__call__'):
            assert verify_par(par)
            return

        else:
            assert verify_par == par
            return

    if not has_iteritems(par):
        raise ValueError('Assertions failed')

    for kw, arg in iteritems(verify_par):
        _verify_deep_assertion(arg, par[kw])


def _verify_assertions(assertions=None, attrs=None, coords=None, variables=None):
    if assertions is None:
        return

    if not has_iteritems(assertions):
        raise TypeError('assertions must be iterable')

    if 'attrs' in assertions:
        _verify_deep_assertion(assertions['attrs'], attrs)

    if 'coords' in assertions:
        _verify_deep_assertion(assertions['coords'], coords)

    if 'variables' in assertions:
        _verify_deep_assertion(assertions['variables'], variables)

    for kw, arg in iteritems(assertions):
        if kw in ['attrs','coords','variables']:
            continue
        _verify_deep_assertion(arg, attrs[kw])



def read_header(fp, header_file=None, parse_vars=False, assertions=None, *args, **kwargs):
    """
    Read a metacsv-formatted header

    Args:
        fp (str or buffer): csv or metacsv-formatted filepath or buffer to read

    Kwargs:
        header_file (str or buffer): optional supplemental yaml header file
        parse_vars (bool): parse compact-style variable definitions (see example)
        assertions (dict-like): dictionary of values to assert in file header

    Returns:
        args
        variables
        coords

    Example:

        >>> import metacsv
        >>> try:
        ...   import StringIO as io
        ... except ImportError:
        ...   import io
        ...
        >>> doc = io.StringIO('''
        ... ---
        ... author: A Person
        ... date:   2000-01-01
        ... variables:
        ...     pop:
        ...       name: Population
        ...       unit: millions
        ...     gdp:
        ...       name: Product
        ...       unit: 2005 $Bn
        ... ...
        ... other data, not csv-formatted
        ... ''')

        >>> attrs, coords, variables = metacsv.read_header(doc, index_col=[0,1])
        >>> variables # doctest: +SKIP
        Variables ...
            gdp:
                name            Product
                unit            2005 $Bn
            pop:
                name            Population
                unit            millions

        >>> attrs # doctest: +SKIP
        Attributes
            author:         A Person
            date:           2000-01-01

        >>> coords
        <Empty Coordinates>

    **parse_vars**

    The read_header argument ``parse_vars`` allows parsing of one-line variable definitions in the format ``var: description [unit]``:

    Example:

        >>> try:
        ...   import StringIO as io
        ... except ImportError:
        ...   import io
        ...
        >>> doc = io.StringIO('''
        ... ---
        ... author: A Person
        ... date:   2000-01-01
        ... variables:
        ...     pop: Population [millions]
        ...     gdp: Product [2005 $Bn]
        ... ...
        ... region,year,pop,gdp
        ... USA,2010,309.3,13599.3
        ... USA,2011,311.7,13817.0
        ... CAN,2010,34.0,1240.0
        ... CAN,2011,34.3,1276.7
        ... ''')

        >>> attrs, coords, variables = metacsv.read_header(doc, parse_vars=True)
        >>> variables # doctest: +SKIP
        Variables
            gdp:
                description     Product
                unit            2005 $Bn
            pop:
                description     Population
                unit            millions
    """

    kwargs = dict(kwargs)

    header = OrderedDict()

    if isinstance(header_file, string_types):
        with open(header_file, 'r') as hf:
            header = ordered_load(hf.read())

    elif header_file is not None:
        header = ordered_load(hf.read())

    if isinstance(fp, string_types):
        with open(fp, 'r') as fp:
            _header = _parse_headered_data(fp)

    else:
        _header = _parse_headered_data(fp)

    header.update(_header)

    kwargs.update({'attrs': header})
    args, kwargs, special = Container.strip_special_attributes(args, kwargs)

    if parse_vars:
        if 'variables' in special:
            for key, var in special['variables'].items():
                special['variables'][key] = Variables.parse_string_var(var)

    attrs = Attributes(None if ('attrs' not in special) else special['attrs'])
    coords = Coordinates(None if ('coords' not in special) else special['coords'])
    variables = Variables(None if ('variables' not in special) else special['variables'])

    _verify_assertions(assertions, attrs=attrs, coords=coords, variables=variables)

    return attrs, coords, variables


def read_csv(fp, header_file=None, parse_vars=False, assertions=None, *args, **kwargs):
    """
    Read a csv or metacsv-formatted csv into a metacsv.DataFrame

    Args:
        fp (str or buffer): csv or metacsv-formatted filepath or buffer to read

    Kwargs:
        header_file (str or buffer): optional supplemental yaml header file
        parse_vars (bool): parse compact-style variable definitions (see example)
        assertions (dict-like): dictionary of values to assert in file header

    *args, **kwargs passed to pandas.read_csv

    Example:

        >>> import metacsv, numpy as np
        >>> try:
        ...   import StringIO as io
        ... except ImportError:
        ...   import io
        ...
        >>> doc = io.StringIO('''
        ... ---
        ... author: A Person
        ... date:   2000-01-01
        ... variables:
        ...     pop:
        ...       name: Population
        ...       unit: millions
        ...     gdp:
        ...       name: Product
        ...       unit: 2005 $Bn
        ... ...
        ... region,year,pop,gdp
        ... USA,2010,309.3,13599.3
        ... USA,2011,311.7,13817.0
        ... CAN,2010,34.0,1240.0
        ... CAN,2011,34.3,1276.7
        ... ''')

        >>> df = metacsv.read_csv(doc, index_col=[0,1])
        >>> df # doctest: +SKIP
        <metacsv.core.containers.DataFrame (4, 2)>
                       pop      gdp
        region year
        USA    2010  309.3  13599.3
               2011  311.7  13817.0
        CAN    2010   34.0   1240.0
               2011   34.3   1276.7
        <BLANKLINE>
        Variables
            gdp:
                name            Product
                unit            2005 $Bn
            pop:
                name            Population
                unit            millions
        Attributes
            author:         A Person
            date:           2000-01-01

    **parse_vars**

    The read-csv argument ``parse_vars`` allows parsing of one-line variable definitions in the format ``var: description [unit]``:

    Example:

        >>> try:
        ...   import StringIO as io
        ... except ImportError:
        ...   import io
        ...
        >>> doc = io.StringIO('''
        ... ---
        ... author: A Person
        ... date:   2000-01-01
        ... variables:
        ...     pop: Population [millions]
        ...     gdp: Product [2005 $Bn]
        ... ...
        ... region,year,pop,gdp
        ... USA,2010,309.3,13599.3
        ... USA,2011,311.7,13817.0
        ... CAN,2010,34.0,1240.0
        ... CAN,2011,34.3,1276.7
        ... ''')

        >>> metacsv.read_csv(doc, index_col=0, parse_vars=True) # doctest: +SKIP
        <metacsv.core.containers.DataFrame (4, 3)>
                year    pop      gdp
        region
        USA     2010  309.3  13599.3
        USA     2011  311.7  13817.0
        CAN     2010   34.0   1240.0
        CAN     2011   34.3   1276.7
        <BLANKLINE>
        Variables
            gdp:
                description     Product
                unit            2005 $Bn
            pop:
                description     Population
                unit            millions
        Attributes
            author:         A Person
            date:           2000-01-01
    """

    kwargs = dict(kwargs)

    squeeze = kwargs.get('squeeze', False)

    # set defaults
    engine = kwargs.pop('engine', 'python')
    kwargs['engine'] = engine

    header = OrderedDict()

    if isinstance(header_file, string_types):
        with open(header_file, 'r') as hf:
            header = ordered_load(hf.read())

    elif header_file is not None:
        header = ordered_load(hf.read())

    if isinstance(fp, string_types):
        with open(fp, 'r') as fp:
            _header = _parse_headered_data(fp)
            data = pd.read_csv(fp, *args, **kwargs)

    else:
        _header = _parse_headered_data(fp)
        data = pd.read_csv(fp, *args, **kwargs)

    header.update(_header)

    kwargs.update({'attrs': header})
    args, kwargs, special = Container.strip_special_attributes(args, kwargs)

    if parse_vars:
        if 'variables' in special:
            for key, var in special['variables'].items():
                special['variables'][key] = Variables.parse_string_var(var)

    if squeeze:
        if len(data.shape) == 1:
            s = Series(data, **special)
            _verify_assertions(assertions, attrs=s.attrs, variables=s.variables, coords=s.coords)
            return s

    df = DataFrame(data, **special)

    if squeeze and df.shape[1] == 1:
        s = Series(df[df.columns[0]], **special)
        _verify_assertions(assertions, attrs=s.attrs, variables=s.variables, coords=s.coords)
        return s
    else:
        _verify_assertions(assertions, attrs=df.attrs, variables=df.variables, coords=df.coords)
        return df


def read_pickle(fp, assertions=None, *args, **kwargs):
    """
    Read a pandas or metacsv pickle file into a metacsv container

    Args:
        fp (str or buffer): ffilepath or buffer to read

    Kwargs:
        assertions (dict-like): dictionary of values to assert in file header

    *args, **kwargs passed to pandas.read_pickle
    """

    return _verify_assertions(pd.read_pickle(fp, *args, **kwargs), assertions)
