#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `metacsv` module."""

from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals
)

import glob, os, pandas as pd

from .. import *

from . import unittest


class TestMetacsv(unittest.TestCase):

    def setUp(self):
        pass

    def test_read_csv(self):
        """Test CSV Reading functionality"""
        
        testdata_prefix = 'metacsv/testsuite/test_data'

        csv1 = parsers.read_csv(os.path.join(testdata_prefix, 'test1.csv'))
        csv2 = pd.read_csv(os.path.join(testdata_prefix, 'test2.csv'))

        assert (csv1.values == csv2.set_index('ind').values).all().all()


    def tearDown(self):
        pass


def suite():
    from .helpers import setup_path
    setup_path()
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMetacsv))
    return suite
