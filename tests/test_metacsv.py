#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `metacsv` module."""

from __future__ import (
    absolute_import,
    division, print_function, with_statement,
    unicode_literals
)

import glob
import os
import xarray as xr
import pandas as pd
import numpy as np
import shutil
import json
import subprocess
import locale
import metacsv
import pytest
from metacsv._compat import text_type


class VersionError(ValueError):
    pass

testdata_prefix = 'tests/test_data'
test_tmp_prefix = 'tests/tmp'

@pytest.yield_fixture(scope='session')
def setup_env():

    if not os.path.isdir(test_tmp_prefix):
        os.makedirs(test_tmp_prefix)

    yield

    if os.path.isdir(test_tmp_prefix):
        shutil.rmtree(test_tmp_prefix)


def test_read_csv(setup_env):
    """CSV Test 1: Check DataFrame data for CSVs with and without yaml headers"""

    csv1 = metacsv.read_csv(os.path.join(
        testdata_prefix, 'test1.csv'))
    csv2 = pd.read_csv(os.path.join(testdata_prefix, 'test2.csv'))

    csv1.__repr__()
    csv2.__repr__()

    assert (
        (csv1.values == csv2.set_index('ind').values).all().all())

def test_coordinate_conversion_to_xarray(setup_env):
    '''CSV Test 2: Make sure only base coordinates are used in determining xarray dimensionality'''

    df = metacsv.read_csv(os.path.join(testdata_prefix, 'test6.csv'))

    df_str = df.__repr__()

    assert df.to_xarray().isnull().sum().col1 == 0
    assert df.to_xarray().isnull().sum().col2 == 0

    # Test automatic coords assignment
    df = metacsv.read_csv(os.path.join(
        testdata_prefix, 'test5.csv'), squeeze=True)

    del df.coords

    ds = df.to_xarray()

    assert len(df.shape) != len(ds.shape)
    assert df.shape[0] == ds.shape[0]
    assert (ds.shape[1] > 1)

def test_for_series_attributes(setup_env):
    '''CSV Test 3: Ensure read_csv preserves attrs with squeeze=True conversion to Series

    This test is incomplete - a complete test would check that attrs are preserved
    when index_col is not set and the index is set by coords. Currently, this
    does not work.
    '''

    s = metacsv.read_csv(os.path.join(
        testdata_prefix, 'test5.csv'), squeeze=True, index_col=[0, 1])

    s.__repr__()

    assert (hasattr(s, 'attrs') and ('author' in s.attrs))
    assert s.attrs['author'] == 'series creator'

def test_write_and_read_equivalency(setup_env):
    '''CSV Test 4: Ensure data and attr consistency after write and re-read'''

    csv1 = metacsv.read_csv(os.path.join(
        testdata_prefix, 'test1.csv'))
    csv1.attrs['other stuff'] = 'this should show up after write'
    csv1['new_col'] = (np.random.random((len(csv1), 1)))
    tmpfile = os.path.join(test_tmp_prefix, 'test_write_1.csv')
    csv1.to_csv(tmpfile)

    csv2 = metacsv.read_csv(tmpfile)

    csv1.__repr__()
    csv2.__repr__()

    assert ((abs(csv1.values - csv2.values) < 1e-7).all().all())
    assert csv1.coords == csv2.coords
    assert csv1.variables == csv2.variables

    with open(tmpfile, 'w+') as tmp:
        csv1.to_csv(tmp)

    with open(tmpfile, 'r') as tmp:
        csv2 = metacsv.read_csv(tmp)

    assert ((abs(csv1.values - csv2.values) < 1e-7).all().all())
    assert csv1.coords == csv2.coords
    assert csv1.variables == csv2.variables

def test_series_conversion_to_xarray(setup_env):
    '''CSV Test 5: Check conversion of metacsv.Series to xarray.DataArray'''

    csv1 = metacsv.read_csv(os.path.join(
        testdata_prefix, 'test5.csv'), squeeze=True)
    assert len(csv1.shape) == 1

    assert csv1.to_xarray().shape == csv1.shape
    assert ((csv1.to_xarray().values == csv1.values).all())

def test_command_line_converter(setup_env):

    convert_script = 'metacsv.scripts.convert'

    testfile = os.path.join(testdata_prefix, 'test6.csv')
    newname = os.path.splitext(os.path.basename(testfile))[0] + '.nc'
    outfile = os.path.join(test_tmp_prefix, newname)

    p = subprocess.Popen(
        ['python', '-m', convert_script, 'netcdf', testfile, outfile],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)

    out, err = p.communicate()
    if len(err.strip()) != 0:
        print(err.strip().decode(locale.getpreferredencoding()))
    assert len(err.strip()) == 0

    df = metacsv.read_csv(testfile)

    with xr.open_dataset(outfile) as ds:
        assert ((abs(df.values - ds.to_dataframe().set_index(
            [i for i in df.coords if i not in df.base_coords]).values) < 1e-7).all().all())

def test_command_line_version_check(setup_env):
    def get_version(readfile):
        version_check_script = 'metacsv.scripts.version'

        p = subprocess.Popen(
            ['python', '-m', version_check_script, readfile],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE)

        out, err = p.communicate()
        if len(err) != 0:
            raise VersionError(err.strip())
        else:
            return out.strip().decode(locale.getpreferredencoding())

    testfile = os.path.join(testdata_prefix, 'test6.csv')

    with pytest.raises(VersionError):
        get_version(testfile)

    testfile = os.path.join(testdata_prefix, 'test5.csv')
    df = metacsv.read_csv(testfile)

    assert get_version(testfile) == df.attrs['version']

def test_xarray_variable_attribute_persistence(setup_env):
    testfile = os.path.join(testdata_prefix, 'test6.csv')
    assert (metacsv.read_csv(
            testfile).to_xarray().col1.attrs['unit'] == 'wigits')

def test_change_dims(setup_env):
    testfile = os.path.join(testdata_prefix, 'test6.csv')
    df = metacsv.read_csv(testfile)

    # Test DataFrame._constructor_sliced
    series = df[df.columns[0]]
    assert (hasattr(series, 'coords'))

    # Test Series._constructor_expanddims
    df2 = metacsv.DataFrame({df.columns[0]: series})
    assert (hasattr(df2, 'coords'))


def test_standalone_properties(setup_env):

    df = metacsv.read_csv(os.path.join(testdata_prefix, 'test3.csv'))

    df.columns = ['index', 'column1', 'column2']
    df.set_index('index', inplace=True)

    variables = metacsv.core.internals.Variables({
        'column1': {
            'units': 'wigits'
        },
        'column2': {
            'units': 'wigits'
        }})

    df.variables = variables

    assert df.variables == variables
    assert df.variables.__repr__() == variables.__repr__()
    assert df.variables[df.columns[1]]['units'] == 'wigits'

    attrs = metacsv.core.internals.Attributes()
    assert attrs == None
    assert not 'author' in attrs.copy()

    with pytest.raises(KeyError):
        del attrs['author']

    with pytest.raises(KeyError):
        err = attrs['author']

    with pytest.raises(KeyError):
        err = attrs.get('author')

    assert attrs.get('author', None) == None

    with pytest.raises(ValueError):
        err = attrs.get('author', 1, 2)

    assert attrs.pop('author', None) == None

    with pytest.raises(KeyError):
        err = attrs.pop('author')

    with pytest.raises(ValueError):
        err = attrs.pop('author', 1, 2)

    assert attrs == None
    assert attrs.__repr__() == '<Empty Attributes>'

    attrs['author'] = 'My Name'
    attrs['contact'] = 'me@email.com'

    assert attrs.pop('author', None) == 'My Name'
    assert attrs.pop('author', None) == None

    df.attrs.update(attrs)
    df.attrs.update({'project': 'metacsv'})

    with pytest.raises(TypeError):
        df.attrs.update(1)

    assert not df.attrs == attrs
    del df.attrs['project']
    assert df.attrs == attrs

    assert df.attrs['contact'] == 'me@email.com'
    assert df.attrs.get('contact') == 'me@email.com'
    assert df.attrs.get('other', 'thing') == 'thing'
    assert df.attrs.pop('contact') == 'me@email.com'
    assert df.attrs.pop('contact', 'nope') == 'nope'
    assert df.attrs != attrs

    attrs['author'] = 'My Name'
    df.variables['column1'] = attrs
    assert df.variables['column1']['author'] == 'My Name'

    var = df.variables.copy()
    assert df.variables == var

    with pytest.raises(TypeError):
        var.parse_string_var(['unit'])

    assert ('description' in var.parse_string_var('variable name [unit]'))
    assert var.parse_string_var('variable [ name') == 'variable [ name'

    with pytest.raises(TypeError):
        df.variables = []

    del df.variables

    # Test round trip
    df2 = metacsv.read_csv(
        os.path.join(testdata_prefix, 'test3.csv'),
        index_col=[0], skiprows=1,
        names=['column1', 'column2'])

    df2.index.names = ['index']

    assert ((df == df2).all().all())

def test_standalone_coords(setup_env):

    with pytest.raises(TypeError):
        coords = metacsv.core.internals.Coordinates({'a': 'b'}, container=[])

    coords = metacsv.core.internals.Coordinates()

    with pytest.raises(ValueError):
        coords.update()

    with pytest.raises(KeyError):
        coords['a']

    assert coords.__repr__() == '<Empty Coordinates>'

    coords.update({'a': None})
    assert coords.__repr__() != '<Empty Coordinates>'


def test_parse_vars(setup_env):
    df = metacsv.read_csv(
        os.path.join(testdata_prefix, 'test8.csv'),
        parse_vars=True,
        index_col=[0,1,2],
        coords={'ind1':None, 'ind2':None, 'ind3':['ind2']})

    assert (df.hasattr(df.variables['col1'], 'description'))
    df.variables['col1']['description'] == 'The first column'
    df.variables['col2']['unit'] == 'digits'


def test_parse_vars(setup_env):

    df = metacsv.read_csv(os.path.join(
        testdata_prefix, 'test7.csv'), parse_vars=True, index_col=0)
    ds = df.to_xarray()

    assert ds.col1.attrs['description'] == 'The first column'
    assert ds.col1.attrs['unit'] == 'wigits'
    assert ds.col2.attrs['description'] == 'The second column'
    assert ds.col2.attrs['unit'] == 'digits'

def test_attr_updating(setup_env):

    df = metacsv.read_csv(os.path.join(testdata_prefix, 'test6.csv'))
    df.coords.update({'ind3': ['s2'], 's2': None})
    coords = df.coords

    # Send to xarray.Dataset
    ds = df.to_xarray()

    del df.coords

    # Create a similarly indexed series by
    # applying coords after the slice operation
    s = df['col1']
    s.coords = coords

    # Send to xarray.DataArray
    da = s.to_xarray()

    assert ((ds.col1 == da).all().all())

    df = metacsv.DataFrame(np.random.random((3,4)))
    df.add_coords()
    del df.coords

    df.index = pd.MultiIndex.from_tuples([('a','x'),('b','y'),('c','z')])
    df.add_coords()


def test_converters(setup_env):

    tmpfile = os.path.join(test_tmp_prefix, 'test_write_1.csv')
    tmpnc = os.path.join(test_tmp_prefix, 'test_write_1.nc')

    df = pd.DataFrame(np.random.random((3,4)), columns=list('abcd'))
    df.index.names = ['ind']

    attrs = {'author': 'My Name'}

    metacsv.to_csv(df, tmpfile, attrs=attrs, coords={'ind': None})
    da = metacsv.to_dataarray(df, attrs=attrs, coords={'ind': None})
    ds1 = metacsv.to_xarray(df, attrs=attrs, coords={'ind': None})
    ds2 = metacsv.to_dataset(df, attrs=attrs, coords={'ind': None})

    df2 = metacsv.DataFrame(df, attrs=attrs)
    df2.add_coords()

    df3 = metacsv.read_csv(tmpfile)

    assert df2.coords == df3.coords

    assert ((ds1 == ds2).all().all())
    assert df.shape[0]*df.shape[1] == da.shape[0]*da.shape[1]

    attrs = metacsv.core.internals.Attributes()
    attrs.update(da.attrs)
    assert df2.attrs == attrs

    df = metacsv.read_csv(os.path.join(testdata_prefix, 'test6.csv'))
    ds = df.to_xarray()
    da = df.to_dataarray()
    assert not ds.col2.isnull().any()

    attrs = df.attrs.copy()
    coords = df.coords.copy()
    variables = df.variables.copy()

    df.columns.names = ['cols']

    s = df.stack('cols')
    metacsv.to_csv(s, tmpfile, attrs={'author': 'my name'})
    s = metacsv.Series(s)
    coords.update({'cols': None})
    s.attrs = attrs
    s.coords = coords
    s.variables = variables

    s.to_xarray()
    s.to_dataarray()
    s.to_dataset()

    with pytest.raises(TypeError):
        metacsv.to_xarray(['a','b','c'])

    metacsv.to_csv(
        os.path.join(testdata_prefix, 'test6.csv'),
        tmpfile,
        attrs={'author': 'test author'},
        variables={'col1': {'unit': 'digits'}})


    df = metacsv.read_csv(tmpfile)
    assert (df.attrs['author']  == 'test author')

    ds = metacsv.to_xarray(tmpfile)
    assert ds.col1.attrs['unit'] == 'digits'


    metacsv.to_netcdf(tmpfile, tmpnc)
    with xr.open_dataset(tmpnc) as ds:
        assert (ds.col1.attrs['unit'] == 'digits')


def test_assertions(setup_env):
    fp = os.path.join(testdata_prefix, 'test7.csv')

    df = metacsv.read_csv(fp, parse_vars=True,
        assertions={'attrs': {'version': 'test5.2016-05-01.01'}})

    df = metacsv.read_csv(fp, parse_vars=True,
        assertions={'attrs': {'version': lambda x: x>'test5.2016-05-01.00'}})

    df = metacsv.read_csv(fp, parse_vars=True,
        assertions={'variables': {'col2': {'unit': 'digits'}}})

def test_header_writer(setup_env):
    fp = os.path.join(testdata_prefix, 'test9.csv')

    attrs = {'author': 'test author', 'contact': 'my.email@isp.net'}
    coords = {'ind1': None, 'ind2': None, 'ind3': 'ind2'}
    variables = {'col1': dict(description='my first column'), 'col2': dict(description='my second column')}

    tmpheader = os.path.join(test_tmp_prefix, 'test_header.header')
    metacsv.to_header(tmpheader, attrs=attrs, coords=coords, variables=variables)

    df = metacsv.read_csv(fp, header_file=tmpheader)

    assert df.attrs == attrs
    assert df.coords == coords
    assert df.variables == variables
