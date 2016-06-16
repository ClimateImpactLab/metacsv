#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `metacsv` module."""

from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals
)

import glob, os, xarray as xr, pandas as pd, numpy as np, shutil, json, subprocess, locale

import metacsv
from . import unittest
from . import helpers

class VersionError(ValueError):
    pass

class MetacsvTestCase(unittest.TestCase):
    testdata_prefix = 'metacsv/testsuite/test_data'
    test_tmp_prefix = 'metacsv/testsuite/tmp'

    def setUp(self):
        if not os.path.isdir(self.test_tmp_prefix):
            os.makedirs(self.test_tmp_prefix)

    def test_read_csv(self):
        """CSV Test 1: Check DataFrame data for CSVs with and without yaml headers"""
        

        csv1 = metacsv.read_csv(os.path.join(self.testdata_prefix, 'test1.csv'))
        csv2 = pd.read_csv(os.path.join(self.testdata_prefix, 'test2.csv'))

        csv1.__repr__()
        csv2.__repr__()

        self.assertTrue((csv1.values == csv2.set_index('ind').values).all().all())


    def test_coordinate_conversion_to_xarray(self):
        '''CSV Test 2: Make sure only base coordinates are used in determining xarray dimensionality'''

        df = metacsv.read_csv(os.path.join(self.testdata_prefix, 'test6.csv'))

        df_str = df.__repr__()

        self.assertEqual(df.to_xarray().isnull().sum().col1, 0)
        self.assertEqual(df.to_xarray().isnull().sum().col2, 0)

        # Test automatic coords assignment
        df = metacsv.read_csv(os.path.join(self.testdata_prefix, 'test5.csv'), squeeze=True)
        del df.coords

        ds = df.to_xarray()

        self.assertNotEqual(len(df.shape), len(ds.shape))
        self.assertEqual(df.shape[0], ds.shape[0])
        self.assertTrue(ds.shape[1] > 1)


    def test_for_series_attributes(self):
        '''CSV Test 3: Ensure read_csv preserves attrs with squeeze=True conversion to Series

        This test is incomplete - a complete test would check that attrs are preserved
        when index_col is not set and the index is set by coords. Currently, this 
        does not work.
        '''

        s = metacsv.read_csv(os.path.join(self.testdata_prefix, 'test5.csv'), squeeze=True, index_col=[0,1])

        s.__repr__()

        self.assertTrue(hasattr(s, 'attrs') and ('author' in s.attrs))
        self.assertEqual(s.attrs['author'], 'series creator')

    def test_write_and_read_equivalency(self):
        '''CSV Test 4: Ensure data and attr consistency after write and re-read'''

        csv1 = metacsv.read_csv(os.path.join(self.testdata_prefix, 'test1.csv'))
        csv1.attrs['other stuff'] = 'this should show up after write'
        csv1['new_col'] = (np.random.random((len(csv1),1)))
        tmpfile = os.path.join(self.test_tmp_prefix, 'test_write_1.csv')
        csv1.to_csv(tmpfile)

        csv2 = metacsv.read_csv(tmpfile)

        csv1.__repr__()
        csv2.__repr__()

        self.assertTrue((abs(csv1.values - csv2.values) < 1e-7).all().all())
        self.assertEqual(csv1.coords, csv2.coords)
        self.assertEqual(csv1.variables , csv2.variables)

        with open(tmpfile, 'w+') as tmp:
            csv1.to_csv(tmp)

        with open(tmpfile, 'r') as tmp:
            csv2 = metacsv.read_csv(tmp)

        self.assertTrue((abs(csv1.values - csv2.values) < 1e-7).all().all())
        self.assertEqual(csv1.coords, csv2.coords)
        self.assertEqual(csv1.variables , csv2.variables)

    def test_series_conversion_to_xarray(self):
        '''CSV Test 5: Check conversion of metacsv.Series to xarray.DataArray'''

        csv1 = metacsv.read_csv(os.path.join(self.testdata_prefix, 'test5.csv'), squeeze=True)
        self.assertEqual(len(csv1.shape), 1)

        self.assertEqual(csv1.to_xarray().shape, csv1.shape)
        self.assertTrue((csv1.to_xarray().values == csv1.values).all())


    def test_command_line_converter(self):
        
        convert_script = 'metacsv/scripts/convert.py'

        testfile = os.path.join(self.testdata_prefix, 'test6.csv')
        newname = os.path.splitext(os.path.basename(testfile))[0] + '.nc'
        outfile = os.path.join(self.test_tmp_prefix, newname)

        p = subprocess.Popen(
            ['python', convert_script, 'netcdf', testfile, outfile], 
                stderr=subprocess.PIPE, 
                stdout=subprocess.PIPE)

        out, err = p.communicate()
        self.assertEqual(len(err.strip()), 0)

        df = metacsv.read_csv(testfile)

        with xr.open_dataset(outfile) as ds:
            self.assertTrue((abs(df.values - ds.to_dataframe().set_index([i for i in df.coords if i not in df.base_coords]).values) < 1e-7).all().all())


    def test_command_line_version_check(self):
        def get_version(readfile):
            version_check_script = 'metacsv/scripts/version.py'


            p = subprocess.Popen(
                ['python',version_check_script,readfile], 
                stderr=subprocess.PIPE, 
                stdout=subprocess.PIPE)

            out, err = p.communicate()
            if len(err) != 0:
                raise VersionError(err.strip())
            else:
                return out.strip().decode(locale.getpreferredencoding())

        testfile = os.path.join(self.testdata_prefix, 'test6.csv')

        with self.assertRaises(VersionError):
            get_version(testfile)

        testfile = os.path.join(self.testdata_prefix, 'test5.csv')
        df = metacsv.read_csv(testfile)

        self.assertEqual(get_version(testfile), df.attrs['version'])

    def test_xarray_variable_attribute_persistence(self):
        testfile = os.path.join(self.testdata_prefix, 'test6.csv')
        self.assertTrue(metacsv.read_csv(testfile).to_xarray().col1.attrs['unit'], 'wigits')

    def test_change_dims(self):
        testfile = os.path.join(self.testdata_prefix, 'test6.csv')
        df = metacsv.read_csv(testfile)

        # Test DataFrame._constructor_sliced
        series = df[df.columns[0]]
        self.assertTrue(hasattr(series, 'coords'))
        
        # Test Series._constructor_expanddims
        df2 = metacsv.DataFrame({df.columns[0]: series})
        self.assertTrue(hasattr(df2, 'coords'))

        # Test DataFrame._constructor_expanddims
        panel = metacsv.Panel({'df': df})
        self.assertTrue(hasattr(panel, 'coords'))

        # Test Panel._constructor_sliced
        df3 = panel['df']
        self.assertTrue(hasattr(df3, 'coords'))

    def test_standalone_properties(self):

        df = metacsv.read_csv(os.path.join(self.testdata_prefix, 'test3.csv'))

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

        self.assertEqual(df.variables, variables)
        self.assertEqual(df.variables.__repr__(), variables.__repr__())
        self.assertEqual(df.variables[df.columns[1]]['units'], 'wigits')

        attrs = metacsv.core.internals.Attributes()
        self.assertEqual(attrs, None)

        self.assertEqual(attrs, None)
        self.assertEqual(attrs.__repr__(), '<Empty Attributes>')

        attrs['author'] = 'My Name'
        attrs['contact'] = 'me@email.com'

        self.assertEqual(attrs.pop('author', None), 'My Name')
        self.assertEqual(attrs.pop('author', None), None)

        df.attrs.update(attrs)
        df.attrs.update({'project': 'metacsv'})

        self.assertNotEqual(df.attrs, attrs)
        del df.attrs['project']
        self.assertEqual(df.attrs, attrs)

        self.assertEqual(df.attrs['contact'], 'me@email.com')
        self.assertEqual(df.attrs.get('contact'), 'me@email.com')
        self.assertEqual(df.attrs.get('other', 'thing'), 'thing')
        self.assertEqual(df.attrs.pop('contact'), 'me@email.com')
        self.assertEqual(df.attrs.pop('contact', 'nope'), 'nope')
        self.assertNotEqual(df.attrs, attrs)

        del df.variables

        # Test round trip
        df2 = metacsv.read_csv(
            os.path.join(self.testdata_prefix, 'test3.csv'),
            index_col=[0], skiprows=1,
            names=['column1', 'column2'])

        df2.index.names = ['index']

        self.assertTrue((df == df2).all().all())


    def tearDown(self):
        if os.path.isdir(self.test_tmp_prefix):
            shutil.rmtree(self.test_tmp_prefix)


def suite():
    from .helpers import setup_path
    setup_path()
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MetacsvTestCase))
    return suite

