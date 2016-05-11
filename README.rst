=======
MetaDoc
=======


.. image:: https://travis-ci.org/delgadom/metadoc.png?branch=master
    :target: https://travis-ci.org/delgadom/metadoc

.. image:: https://badge.fury.io/py/metadoc.png
    :target: http://badge.fury.io/py/metadoc

.. image:: https://coveralls.io/repos/github/delgadom/metadoc/badge.png?branch=master :target: https://coveralls.io/github/delgadom/metadoc?branch=master

.. image:: https://pypip.in/d/metadoc/badge.png
        :target: https://crate.io/packages/metadoc?version=latest


``metadoc`` - Tools for documentation-aware data reading, writing, and analysis

Features
--------

Read in CSV data with a yaml-compliant header directly into 
a `pandas` `Series`, `DataFrame`, or `Panel` or an `xarray` 
`DataArray` or `Dataset`:

.. code-block:: python

    >>> import metadoc, StringIO
    >>> doc = StringIO('''
    ---
    format: yaml
    author: A Person
    date:   2000-01-01
    variables:
        pop: {name: Population, unit: millions}
        gdp: {name: Product, unit: 2005 $Bn}
    coords:
        region
        year
    ---
    region, year, pop, gdp
    USA,2010,309.3,13599.3
    USA,2011,311.7,13817.0
    CAN,2010,34.0,1240.0
    CAN,2011,34.3,1276.7
    ''')
    
    >>> df = metadoc.read_csv(doc, index_cols=[0,1])
    >>> df
                pop   gdp
    region year 
    USA    2010 309.3 13599.3
    USA    2011 311.7 13817.0
    CAN    2010  34.0  1240.0
    CAN    2011  34.3  1276.7



* TODO

==============  ==========================================================
Python support  Python 2.7, >= 3.3
Source          https://github.com/delgadom/metadoc
Docs            http://metadoc.rtfd.org
Changelog       http://metadoc.readthedocs.org/en/latest/history.html
API             http://metadoc.readthedocs.org/en/latest/api.html
Issues          https://github.com/delgadom/metadoc/issues
Travis          http://travis-ci.org/delgadom/metadoc
Test coverage   https://coveralls.io/r/delgadom/metadoc
pypi            https://pypi.python.org/pypi/metadoc
Ohloh           https://www.ohloh.net/p/metadoc
License         `BSD`_.
git repo        .. code-block:: bash

                    $ git clone https://github.com/delgadom/metadoc.git
install dev     .. code-block:: bash

                    $ git clone https://github.com/delgadom/metadoc.git metadoc
                    $ cd ./metadoc
                    $ virtualenv .env
                    $ source .env/bin/activate
                    $ pip install -e .
tests           .. code-block:: bash

                    $ python setup.py test
==============  ==========================================================

.. _BSD: http://opensource.org/licenses/BSD-3-Clause
.. _Documentation: http://metadoc.readthedocs.org/en/latest/
.. _API: http://metadoc.readthedocs.org/en/latest/api.html
