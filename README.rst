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

See the full documentation at ReadTheDocs_ 

.. _ReadTheDocs: http://metacsv.rtfd.org

Features
=========

Read in CSV data with a yaml-compliant header directly into 
a `pandas` `Series`, `DataFrame`, or `Panel` or an `xarray` 
`DataArray` or `Dataset`.

Data specification
----------------------------

Data can be specified using a yaml-formatted header, with the doc-separation string
above and below the yaml block. Only one yaml block is allowed. If the doc-separation
string is not the first (non-whitespace) line in the file, all of the file's contents
will be interpreted by the csv reader. The yaml data can have arbitrary complexity.

.. code-block:: python

    >>> import metacsv, io
    >>> doc = io.StringIO('''
    ---
    author: A Person
    date:   2000-01-01
    variables:
        pop: {name: Population, unit: millions}
        gdp: {name: Product, unit: 2005 $Bn}
    coords:
        region: !!null
        regname: region
        year: !!null
    ---
    region,regname,year,pop,gdp
    USA,United States,2010,309.3,13599.3
    USA,United States,2011,311.7,13817.0
    CAN,Canada,2010,34.0,1240.0
    CAN,Canada,2011,34.3,1276.7
    ''')
    

Using MetaCSV-formatted files in python
--------------------------------------------

Read MetaCSV-formatted data into python using pandas-like syntax: 

.. code-block:: python

    >>> df = metacsv.read_csv(doc, index_col=[0,1,2])
    >>> df
    <metacsv.core.containers.DataFrame (4, 2)>
                                 pop      gdp
    region regname       year
    USA    United States 2010  309.3  13599.3
                         2011  311.7  13817.0
    CAN    Canada        2010   34.0   1240.0
                         2011   34.3   1276.7
    
    Coordinates
      * region     (region) object CAN, USA
      * year       (year) int64 2010, 2011
        regname    (region) object Canada...
    Variables
        pop
        gdp
    Attributes
        date: 2000-01-01
        author: A Person

Exporting MetaCSV data to other formats
-----------------------------------------------

pandas
~~~~~~~~~~~~~~~

The coordinates and MetaCSV attributes can be easily stripped from a MetaCSV Container:

.. code-block:: python
    >>> df.to_pandas()
                                 pop      gdp
    region regname       year
    USA    United States 2010  309.3  13599.3
                         2011  311.7  13817.0
    CAN    Canada        2010   34.0   1240.0
                         2011   34.3   1276.7



xarray/netCDF
~~~~~~~~~~~~~~~

.. code-block:: python

    >>> ds = df.to_xarray()
    >>> ds
    <xarray.Dataset>
    Dimensions:  (region: 2, year: 2)
    Coordinates:
      * region   (region) object 'USA' 'CAN'
      * year     (year) int64 2010 2011
        regname  (region) object 'United States' 'Canada'
    Data variables:
        pop      (region, year) float64 309.3 311.7 34.0 34.3
        gdp      (region, year) float64 1.36e+04 1.382e+04 1.24e+03 1.277e+03
    Attributes:
        date: 2000-01-01
        author: A Person
    >>> ds.to_netcdf('my_data_netcdf.nc')

Currently, MetaCSV only supports conversion back to CSV and to 
netCDF through the `xarray` module. However, feel free to suggest 
additional features and to contribute your own!


TODO
============

.. include:: TODO


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
