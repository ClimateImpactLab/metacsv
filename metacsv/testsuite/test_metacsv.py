#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `metacsv` module."""

from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals
)

import glob, os, pandas as pd, numpy as np, shutil, json

from .. import *

from . import unittest


class MetacsvTestCase(unittest.TestCase):
    testdata_prefix = 'metacsv/testsuite/test_data'
    test_tmp_prefix = 'metacsv/testsuite/tmp'

    def setUp(self):
        if not os.path.isdir(self.test_tmp_prefix):
            os.makedirs(self.test_tmp_prefix)

    def test_read_csv(self):
        """CSV Test 1: Check DataFrame data for CSVs with and without yaml headers"""
        

        csv1 = parsers.read_csv(os.path.join(self.testdata_prefix, 'test1.csv'))
        csv2 = pd.read_csv(os.path.join(self.testdata_prefix, 'test2.csv'))

        self.assertTrue((csv1.values == csv2.set_index('ind').values).all().all())


    def test_coordinate_conversion_to_xarray(self):
        '''CSV Test 2: Make sure only base coordinates are used in determining xarray dimensionality'''

        df = parsers.read_csv(os.path.join(self.testdata_prefix, 'test6.csv'))

        self.assertEqual(df.to_xarray().isnull().sum().col1, 0)
        self.assertEqual(df.to_xarray().isnull().sum().col2, 0)

    def test_for_series_attributes(self):
        '''CSV Test 3: Ensure read_csv preserves attrs with squeeze=True conversion to Series

        This test is incomplete - a complete test would check that attrs are preserved
        when index_col is not set and the index is set by coords. Currently, this 
        does not work.
        '''

        s = parsers.read_csv(os.path.join(self.testdata_prefix, 'test5.csv'), squeeze=True, index_col=[0,1])

        self.assertTrue(hasattr(s, 'attrs') and ('author' in s.attrs))
        self.assertEqual(s.attrs['author'], 'series creator')

    def test_write_and_read_equivalency(self):
        '''CSV Test 4: Ensure data and attr consistency after write and re-read'''

        csv1 = parsers.read_csv(os.path.join(self.testdata_prefix, 'test1.csv'))
        csv1.attrs['other stuff'] = 'this should show up after write'
        csv1['new_col'] = (np.random.random((len(csv1),1)))
        tmpfile = os.path.join(self.test_tmp_prefix, 'test_write_1.csv')
        csv1.to_csv(tmpfile)

        csv2 = parsers.read_csv(tmpfile)

        self.assertTrue((abs(csv1.values - csv2.values) < 1e-7).all().all())
        self.assertEqual(csv1.coords, csv2.coords)
        self.assertEqual(csv1.variables._variables , csv2.variables._variables)


    def tearDown(self):
        if os.path.isdir(self.test_tmp_prefix):
            shutil.rmtree(self.test_tmp_prefix)


def suite():
    from .helpers import setup_path
    setup_path()
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MetacsvTestCase))
    return suite

