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


class TestMetacsv(unittest.TestCase):
    testdata_prefix = 'metacsv/testsuite/test_data'
    test_tmp_prefix = 'metacsv/testsuite/tmp'

    def setUp(self):
        if not os.path.isdir(self.test_tmp_prefix):
            os.makedirs(self.test_tmp_prefix)

    def test_read_csv(self):
        """Test CSV Reading functionality"""
        

        csv1 = parsers.read_csv(os.path.join(self.testdata_prefix, 'test1.csv'))
        csv2 = pd.read_csv(os.path.join(self.testdata_prefix, 'test2.csv'))

        assert (csv1.values == csv2.set_index('ind').values).all().all()


    def test_coordinate_conversion_to_xarray(self):
        df = parsers.read_csv(os.path.join(self.testdata_prefix, 'test6.csv'))

        assert df.to_xarray().isnull().sum().col1 == 0
        assert df.to_xarray().isnull().sum().col2 == 0

    def test_for_series_attributes(self):
        s = parsers.read_csv(os.path.join(self.testdata_prefix, 'test5.csv'), squeeze=True, index_col=[0,1])\

        assert hasattr(s, 'attrs') and ('author' in s.attrs)
        assert s.attrs['author'] == 'series creator'

    def test_write_and_read_equivalency(self):
        csv1 = parsers.read_csv(os.path.join(self.testdata_prefix, 'test1.csv'))
        csv1.attrs['other stuff'] = 'this should show up after write'
        csv1['new_col'] = (np.random.random((len(csv1),1))*100).astype('int')
        tmpfile = os.path.join(self.test_tmp_prefix, 'test_write_1.csv')
        csv1.to_csv(tmpfile)

        csv2 = parsers.read_csv(tmpfile)

        assert (csv1.values == csv2.values).all().all()
        assert csv1.coords == csv2.coords
        assert csv1.variables._variables == csv2.variables._variables


    def tearDown(self):
        if os.path.isdir(self.test_tmp_prefix):
            shutil.rmtree(self.test_tmp_prefix)


def suite():
    from .helpers import setup_path
    setup_path()
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMetacsv))
    return suite

