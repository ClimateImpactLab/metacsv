=======
MetaCSV
=======


.. image:: https://travis-ci.org/delgadom/metacsv.png?branch=master
    :target: https://travis-ci.org/delgadom/metacsv

.. image:: https://badge.fury.io/py/metacsv.png
    :target: http://badge.fury.io/py/metacsv

.. image:: https://coveralls.io/repos/github/delgadom/metacsv/badge.png?branch=master :target: https://coveralls.io/github/delgadom/metacsv?branch=master

.. image:: https://pypip.in/d/metacsv/badge.png
        :target: https://crate.io/packages/metacsv?version=latest


``metacsv`` - Tools for documentation-aware data reading, writing, and analysis

Features
--------

Read in CSV data with a yaml-compliant header directly into 
a `pandas` `Series`, `DataFrame`, or `Panel` or an `xarray` 
`DataArray` or `Dataset`:

.. code-block:: python

    >>> import metacsv
    >>> doc = metacsv._compat.StringIO('''
    ---
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
    
    >>> df = metacsv.read_csv(doc, index_cols=[0,1])
    >>> df
    <metacsv.core.containers.DataFrame (4,2)>
                pop   gdp
    region year 
    USA    2010 309.3 13599.3
    USA    2011 311.7 13817.0
    CAN    2010  34.0  1240.0
    CAN    2011  34.3  1276.7
    
    Coordinates:
       * region (region) object USA CAN
       * year   (year) int16 2010 2011
    Variables:
         pop
         gdp
    Attributes:
        author: A Person
        date: 2000-01-01
    
    >>> df.to_xarray()
    <xarray.Dataset>
    Coordinates:
       * region (region) object USA CAN
       * year   (year) int16 2010 2011
    Variables:
         pop (region, year) 309.3 311.7 34.0 34.3
         gdp (region, year) 13599.3 13817.0 1240.0 ...
    Attributes:
        author: A Person
        date: 2000-01-01

* TODO

==============  ==========================================================
Python support  Python 2.7, >= 3.3
Source          https://github.com/delgadom/metacsv
Docs            http://metacsv.rtfd.org
Changelog       http://metacsv.readthedocs.org/en/latest/history.html
API             http://metacsv.readthedocs.org/en/latest/api.html
Issues          https://github.com/delgadom/metacsv/issues
Travis          http://travis-ci.org/delgadom/metacsv
Test coverage   https://coveralls.io/r/delgadom/metacsv
pypi            https://pypi.python.org/pypi/metacsv
Ohloh           https://www.ohloh.net/p/metacsv
License         `BSD`_.
git repo        .. code-block:: bash

                    $ git clone https://github.com/delgadom/metacsv.git
install dev     .. code-block:: bash

                    $ git clone https://github.com/delgadom/metacsv.git metacsv
                    $ cd ./metacsv
                    $ virtualenv .env
                    $ source .env/bin/activate
                    $ pip install -e .
tests           .. code-block:: bash

                    $ python setup.py test
==============  ==========================================================

.. _BSD: http://opensource.org/licenses/BSD-3-Clause
.. _Documentation: http://metacsv.readthedocs.org/en/latest/
.. _API: http://metacsv.readthedocs.org/en/latest/api.html
