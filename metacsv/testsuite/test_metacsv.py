#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `metacsv` module."""

from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals
)

import glob, os, xarray as xr, pandas as pd, numpy as np, shutil, json

import metacsv
from . import unittest
from . import helpers


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

        df.__repr__()

        self.assertEqual(df.to_xarray().isnull().sum().col1, 0)
        self.assertEqual(df.to_xarray().isnull().sum().col2, 0)

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
        self.assertEqual(csv1.variables._variables , csv2.variables._variables)

        with open(tmpfile, 'w+') as tmp:
            csv1.to_csv(tmp)

        with open(tmpfile, 'r') as tmp:
            csv2 = metacsv.read_csv(tmp)

        self.assertTrue((abs(csv1.values - csv2.values) < 1e-7).all().all())
        self.assertEqual(csv1.coords, csv2.coords)
        self.assertEqual(csv1.variables._variables , csv2.variables._variables)


    def test_command_line_interface(self):
        def script_to_netcdf(readfile, outfile):
            os.system('python {s} netcdf "{fp}" "{dest}"'.format(
                s='metacsv/scripts/convert.py',
                fp=readfile,
                dest = outfile))

        testfile = os.path.join(self.testdata_prefix, 'test6.csv')
        newname = os.path.splitext(os.path.basename(testfile))[0] + '.nc'
        outfile = os.path.join(self.test_tmp_prefix, newname)

        with helpers.captureStdErr(script_to_netcdf, testfile, outfile) as stdout:
            self.assertTrue((stdout is None) or (stdout == ''))

        df = metacsv.read_csv(testfile)
        with xr.open_dataset(outfile) as ds:

            self.assertTrue((abs(df.values - ds.to_dataframe().set_index([i for i in df.coords if i not in df.base_coords]).values) < 1e-7).all().all())

    def tearDown(self):
        if os.path.isdir(self.test_tmp_prefix):
            shutil.rmtree(self.test_tmp_prefix)


def suite():
    from .helpers import setup_path
    setup_path()
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MetacsvTestCase))
    return suite

