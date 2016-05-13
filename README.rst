=======
MetaCSV
=======


.. image:: https://travis-ci.org/delgadom/metacsv.svg?branch=master
    :target: https://travis-ci.org/delgadom/metacsv

.. image:: https://badge.fury.io/py/metacsv.svg
    :target: https://badge.fury.io/py/metacsv

.. image:: https://coveralls.io/repos/github/delgadom/metacsv/badge.svg?branch=master 
    :target: https://coveralls.io/github/delgadom/metacsv?branch=master


``metacsv`` - Tools for documentation-aware data reading, writing, and analysis

See the full documentation at ReadTheDocs_ 

.. _ReadTheDocs: http://metacsv.rtfd.org

Overview
=========

Read in CSV data with a yaml-compliant header directly into 
a ``pandas`` ``Series``, ``DataFrame``, or ``Panel`` or an ``xarray`` 
``DataArray`` or ``Dataset``.

Data specification
----------------------------

Data can be specified using a yaml-formatted header, with the doc-separation 
string (``---``) above and below the yaml block. Only one yaml block is allowed. 
If the doc-separation string is not the first (non-whitespace) line in the file, 
all of the file's contents will be interpreted by the csv reader. The yaml data 
can have arbitrary complexity.

.. code-block:: python

    >>> import metacsv, io
    >>> doc = io.StringIO('''
    ---
    author: A Person
    date:   2000-01-01
    variables:
        pop:
          name: Population
          unit: millions
        gdp:
          name: Product
          unit: 2005 $Bn
    ---
    region,year,pop,gdp
    USA,2010,309.3,13599.3
    USA,2011,311.7,13817.0
    CAN,2010,34.0,1240.0
    CAN,2011,34.3,1276.7
    ''')
    

Special attributes
~~~~~~~~~~~~~~~~~~~~~~~

The ``coords`` and ``variables`` attributes are keywords and are not simply 
passed to the MetaCSV object's ``attrs`` attribute.

``variables`` describes columns in the resulting ``DataFrame`` or 
``Data variables`` in the resulting ``xarray.Dataset``. Variables is not used 
when the CSV has only one column and the argument ``squeeze=True`` is passed to 
``read_csv``.

``coords`` describes indices in the resulting ``DataFrame``/``Series``, or 
``Coordinates`` in the resulting ``xarray.Dataset/xarray.DataArray``. 
Coordinates are categorical or independent variables which index the object's 
``values``. 



Using MetaCSV-formatted files in python
--------------------------------------------

Read MetaCSV-formatted data into python using pandas-like syntax: 

.. code-block:: python

    >>> metacsv.read_csv(doc, index_col=[0,1])
    >>> df
    <metacsv.core.containers.DataFrame (4, 2)>
                   pop      gdp
    region year
    USA    2010  309.3  13599.3
           2011  311.7  13817.0
    CAN    2010   34.0   1240.0
           2011   34.3   1276.7
    
    Coordinates
      * region     (region) object CAN, USA
      * year       (year) int64 2010, 2011
    Variables
        pop
        gdp
    Attributes
        date: 2000-01-01
        author: A Person

Exporting MetaCSV data to other formats
-----------------------------------------------

CSV
~~~~~~~~~

A MetaCSV ``Series`` or ``DataFrame`` can be written as a yaml-prefixed CSV 
using the same ``to_csv`` syntax as it's ``pandas`` counterpart:

.. code-block:: python

    >>> df.attrs['new attribute'] = 'changed in python!'
    >>> # includes changes to data, attributes, variables, and coordinates
    ... df.to_csv('my_new_data.csv')




pandas
~~~~~~~~~~~~~~~

The coordinates and MetaCSV attributes can be easily stripped from a MetaCSV 
Container:

.. code-block:: python

    >>> df.to_pandas()
                   pop      gdp
    region year
    USA    2010  309.3  13599.3
           2011  311.7  13817.0
    CAN    2010   34.0   1240.0
           2011   34.3   1276.7



xarray/netCDF
~~~~~~~~~~~~~~~

``xarray``__ provides a pandas-like interface to operating on indexed ``ndarray`` 
data. It is modeled on the ``netCDF`` data storage format used frequently in 
climate science, but is useful for many applications with higher-order data.

.. __: http://xarray.pydata.org/


.. code-block:: python

    >>> ds = df.to_xarray()
    >>> ds
    <xarray.Dataset>
    Dimensions:  (region: 2, year: 2)
    Coordinates:
      * region   (region) object 'USA' 'CAN'
      * year     (year) int64 2010 2011
    Data variables:
        pop      (region, year) float64 309.3 311.7 34.0 34.3
        gdp      (region, year) float64 1.36e+04 1.382e+04 1.24e+03 1.277e+03
    Attributes:
        date: 2000-01-01
        author: A Person
    >>> ds.to_netcdf('my_netcdf_data.nc')

Others
~~~~~~~~~

Currently, MetaCSV only supports conversion back to CSV and to 
netCDF through the ``xarray`` module. However, feel free to suggest 
additional features and to contribute your own!


TODO
============

* Make ``coords`` and ``attrs`` persistent across slicing operations 
  (try ``df['pop'].to_xarray()`` from above example and watch it 
  fail...)

* Improve hooks between ``pandas`` and ``metacsv``:

  - update ``coord`` names on ``df.index.names`` assignment
  - update ``coords`` on stack/unstack
  - update ``coords`` on 

* Handle attributes indexed by coord/variable names --> assign to 
  coord/variable-specific ``attrs``

* Let's start an issue tracker and get rid of this section!

* Should we rethink "special attributes," e.g. coords? Maybe these should 
  have some special prefix like ``_coords`` when included in yaml headers to 
  avoid confusion with other generic attributes...

* Allow special attributes (``coords``, ``variables``) in ``read_csv`` call

* Allow external file headers

* Write tests

* Write documentation

* Maybe steal xarray's coordinate handling and save ourselves a whole lotta 
  work?


Feature Requests
==================
* Create syntax for ``multi-csv`` --> ``Panel`` or combining using filename 
  regex 
* Eventually? allow for on-disk manipulation of many/large files with 
  dask/xarray 
* Eventually? add xml, SQL, other structured syntax language conversions




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
