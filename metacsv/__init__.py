#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

MetaCSV
-------

Tools for documentation-aware data reading, writing, and analysis

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

from metacsv.__about__ import (
    __title__,
    __package_name__,
    __description__,
    __version__,
    __license__,
    __copyright__)

from metacsv.core import *

from metacsv.io.parsers import (
    read_header,
    read_csv,
    read_pickle)

from metacsv.io.converters import (
    to_dataset,
    to_dataarray,
    to_xarray,
    to_netcdf,
    to_pandas,
    to_csv,
    to_header)