
from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import pandas as pd
import re
from .yaml_tools import ordered_load
from .._compat import string_types, has_iteritems, iteritems
from ..core.internals import Container, Variables
from ..core.containers import Series, DataFrame, Panel


def find_yaml_start(line):
    return re.search(r'^\s*-{3,}\s*$', line) is not None


def find_yaml_stop(line):
    return re.search(r'^\s*\.{3,}\s*$', line) is not None


def _parse_headered_data(fp, *args, **kwargs):

    # Check for a yaml parse break at the top of the file
    # if there is not one, go back to the top and read like a
    # normal CSV
    loc = fp.tell()

    nextline = ''

    while re.search(r'^[\s\n\r]*$', nextline):
        nextline = next(fp)

    if not find_yaml_start(nextline):
        fp.seek(loc)
        return {}, pd.read_csv(fp, *args, **kwargs)

    yaml_text = ''
    this_line = ''

    while not find_yaml_stop(this_line):
        yaml_text += '\n' + this_line.rstrip('\n')
        this_line = next(fp)

    header = ordered_load(yaml_text)
    data = pd.read_csv(fp, *args, **kwargs)

    return header, data

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


def _verify_assertions(container, assertions=None):
    if assertions is None:
        return container

    if not has_iteritems(assertions):
        raise TypeError('assertions must be ')
    
    for par in ['attrs', 'coords', 'variables']:
        if par in assertions:
            _verify_deep_assertion(assertions[par], container.__getitem__(par))

    for kw, arg in iteritems(assertions):
        _verify_deep_assertion(arg, container.attrs[kw])

    return container

def read_csv(string_or_buffer, header_file=None, parse_vars=False, assertions=None, *args, **kwargs):

    kwargs = dict(kwargs)

    squeeze = kwargs.get('squeeze', False)

    # set defaults
    engine = kwargs.pop('engine', 'python')
    kwargs['engine'] = engine

    header = {}

    if isinstance(header_file, string_types):
        with open(header_file, 'r') as hf:
            header = yaml.load(hf.read())

    elif header_file is not None:
        header = yaml.load(hf.read())

    if isinstance(string_or_buffer, string_types):
        with open(string_or_buffer, 'r') as fp:
            _header, data = _parse_headered_data(fp, *args, **kwargs)

    else:
        _header, data = _parse_headered_data(string_or_buffer, *args, **kwargs)

    header.update(_header)

    kwargs.update({'attrs': header})
    args, kwargs, special = Container.strip_special_attributes(args, kwargs)

    if parse_vars:
        if 'variables' in special:
            for key, var in special['variables'].items():
                special['variables'][key] = Variables.parse_string_var(var)

    if squeeze:
        if len(data.shape) == 1:
            return _verify_assertions(Series(data, **special), assertions)

    df = DataFrame(data, **special)

    if squeeze and df.shape[1] == 1:
        return _verify_assertions(Series(df[df.columns[0]], **special), assertions)
    else:
        return _verify_assertions(df, assertions)


def read_pickle(string_or_buffer, assertions=None):
    return _verify_assertions(pd.read_pickle(string_or_buffer), assertions)