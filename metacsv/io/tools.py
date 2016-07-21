'''
Private tools supporting conversion between metacsv-compatible types
'''

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import pandas as pd
import numpy as np
import xarray as xr

from .._compat import string_types, stream_types, BytesIO, StringIO


def _update_or_return_attribute(container, attribute_name, attribute_value=None, inplace=False):
    
    return_value = None

    if attribute_value is not None:
        if hasattr(container, attribute_name) and container.__getattr__(attribute_name) == None:
            if inplace:
                container.__getattr__(attribute_name).update(attribute_value)

            else:
                return_value = container.__getattr__(attribute_name).copy()
                return_value.update(attribute_value)
        else:
            if inplace:
                container.__getattr__(attribute_name).update(attribute_value)
            else:
                return_value = type(container.__getattr__(attribute_name))(attribute_value)

    else:
        return_value = container.__getattr__(attribute_name).copy()

    return return_value



def _parse_args(container, attrs, coords, variables, inplace=False):

    attrs = _update_or_return_attribute(container, 'attrs', attrs, inplace)
    coords = _update_or_return_attribute(container, 'coords', coords, inplace)
    variables = _update_or_return_attribute(container, 'variables', variables, inplace)

    if not inplace:
        return attrs, coords, variables