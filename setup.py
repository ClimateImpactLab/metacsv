#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

about = {}
with open("metacsv/__about__.py") as fp:
    exec(fp.read(), about)


install_reqs = [
    'pandas>=0.17',
    'numpy>1.10',
    'xarray>=0.7',
    'pyyaml']

tests_reqs = install_reqs + ['pytest >= 2.7.1']

if sys.version_info < (2, 7):
    install_reqs += ['argparse']
    tests_reqs += ['unittest2']

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

if sys.argv[-1] == 'info':
    for k, v in about.items():
        print('%s: %s' % (k, v))
    sys.exit()

readme = open('README.rst').read()
history = open('CHANGES').read().replace('.. :changelog:', '')

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme + '\n\n' + history,
    author=about['__author__'],
    author_email=about['__email__'],
    url='https://github.com/delgadom/metacsv',
    packages=find_packages(exclude=['docs']),
    include_package_data=True,
    install_requires=install_reqs,
    tests_require=tests_reqs,
    license=about['__license__'],
    keywords=about['__title__'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
    test_suite='metacsv.testsuite',
)
