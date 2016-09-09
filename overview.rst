=======
MetaCSV
=======


.. image:: https://img.shields.io/travis/ClimateImpactLab/metacsv/master.svg?style=flat-square
    :target: https://travis-ci.org/ClimateImpactLab/metacsv

.. image:: https://img.shields.io/pypi/v/metacsv.svg?style=flat-square
    :target: https://pypi.python.org/pypi/MetaCSV

.. image:: https://img.shields.io/coveralls/delgadom/metacsv/master.svg?style=flat-square
    :target: https://coveralls.io/github/delgadom/metacsv?branch=master

.. image:: https://img.shields.io/pypi/pyversions/metacsv.svg?style=flat-square
    :target: https://pypi.python.org/pypi/MetaCSV

.. image:: https://anaconda.org/delgadom/metacsv/badges/version.svg
    :target: https://anaconda.org/delgadom/metacsv

.. image:: https://anaconda.org/delgadom/metacsv/badges/downloads.svg
    :target: https://anaconda.org/delgadom/metacsv

``metacsv`` - Tools for documentation-aware data reading, writing, and analysis

See the full documentation at ReadTheDocs_ 

.. _ReadTheDocs: http://cli-metacsv.rtfd.io

Overview
=========

**MetaCSV** provides tools to read in CSV data with a yaml-compliant header 
directly into a ``pandas`` ``Series``, ``DataFrame``, or ``Panel`` or an 
``xarray`` ``DataArray`` or ``Dataset``.

Data specification
----------------------------

Data can be specified using a yaml-formatted header, with the YAML *start-mark*
string (``---``) above and the YAML *end-mark* string (``...``) below the yaml 
block. Only one yaml block is allowed. If the doc-separation string is not the 
first (non-whitespace) line in the file, all of the file's contents will be 
interpreted by the csv reader. The yaml data can have arbitrary complexity.

.. code-block:: python

    >>> import metacsv, numpy as np, 
    >>> import StringIO as io # import io for python 3
    >>> doc = io.StringIO('''
    ---
    author: A Person
    date:   2000-12-31
    variables:
        pop:
          name: Population
          unit: millions
        gdp:
          name: Product
          unit: 2005 $Bn
    ...
    region,year,pop,gdp
    USA,2010,309.3,13599.3
    USA,2011,311.7,13817.0
    CAN,2010,34.0,1240.0
    CAN,2011,34.3,1276.7
    ''')



Using MetaCSV-formatted files in python
--------------------------------------------


Read MetaCSV-formatted data into python using pandas-like syntax: 

.. code-block:: python

    >>> df = metacsv.read_csv(doc, index_col=[0,1])
    >>> df
    <metacsv.core.containers.DataFrame (4, 2)>
                   pop      gdp
    region year
    USA    2010  309.3  13599.3
           2011  311.7  13817.0
    CAN    2010   34.0   1240.0
           2011   34.3   1276.7
    
    Variables
        gdp:       OrderedDict([('name', 'Product'), ('unit', '2005 $Bn')])
        pop:       OrderedDict([('name', 'Population'), ('unit', 'millions')])
    Attributes
        date:      2000-12-31
        author:    A Person

These properties can be transferred from one data container to another:

.. code-block:: python

    >>> s = metacsv.Series(np.random.random(6))
    >>> s
    <metacsv.core.containers.Series (6,)>
    0    0.881924
    1    0.556330
    2    0.554700
    3    0.221284
    4    0.970801
    5    0.946414
    dtype: float64
    >>> s.attrs = df.attrs
    >>> s
    <metacsv.core.containers.Series (6,)>
    0    0.881924
    1    0.556330
    2    0.554700
    3    0.221284
    4    0.970801
    5    0.946414
    dtype: float64

    Attributes
        date:      2000-12-31
        author:    A Person
    

All MetaCSV attributes, including the ``attrs`` Attribute object, can be copied, 
assigned to new objects, and deleted. Since these attributes are largely 
unstable across normal pandas data processing, it is recommended that attributes 
be copied before data work is attempted and then reassigned before IO 
conversions.


Exporting MetaCSV data to other formats
-----------------------------------------------

CSV
~~~~~~~~~

A MetaCSV ``Series`` or ``DataFrame`` can be written as a yaml-prefixed CSV 
using the same ``to_csv`` syntax as it's ``pandas`` counterpart:

.. code-block:: python

    >>> df.attrs['new attribute'] = 'changed in python!'
    >>> df.to_csv('my_new_data.csv')

The resulting csv will include a yaml-formatted header with the original 
metadata updated to include attr['new attribute'].,


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

`xArray <http://xarray.pydata.org/>`_ provides a pandas-like interface to 
operating on indexed ``ndarray`` data. It is modeled on the ``netCDF`` data 
storage format used frequently in climate science, but is useful for many 
applications with higher-order data.



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
        date: 2000-12-31
        author: A Person
    >>> ds.to_netcdf('my_netcdf_data.nc')

Pickling
~~~~~~~~~

Pickling works just like pandas.

.. code-block:: python

    >>> df.to_pickle('my_metacsv_pickle.pkl')
    >>> metacsv.read_pickle('my_metacsv_pickle.pkl')
    <metacsv.core.containers.DataFrame (4, 2)>
                   pop      gdp
    region year
    USA    2010  309.3  13599.3
           2011  311.7  13817.0
    CAN    2010   34.0   1240.0
           2011   34.3   1276.7

    Variables
        gdp:       OrderedDict([('name', 'Product'), ('unit', '2005 $Bn')])
        pop:       OrderedDict([('name', 'Population'), ('unit', 'millions')])
    Attributes
        date:      2000-12-31
        author:    A Person



Others
~~~~~~~~~

Currently, MetaCSV only supports conversion to CSV and to netCDF through the 
``xarray`` module. However, feel free to suggest additional features and to 
contribute your own!



Conversion to other types on the fly
-----------------------------------------------

Special conversion utilities allow you to convert any metacsv, pandas, or xarray 
container or a CSV filepath into any other type in this group.

All of these conversion utilities are also methods on metacsv containers.

* to_csv

``to_csv`` allows you to write any container or csv file to a metacsv-formatted 
csv file. Keyword arguments ``attrs``, ``coords``, and ``variables`` will be 
attached to the data before it is written. Any conflicts in these attributes 
will be updated with the arguments to this function

.. code-block:: python

    >>> import pandas as pd, numpy as np, xarray as xr, metacsv
    >>> df = pd.DataFrame(np.random.random((3,4)), columns=list('abcd'))
    >>> df
              a         b         c         d
    0  0.558083  0.665184  0.226173  0.339905
    1  0.541712  0.835804  0.326078  0.179103
    2  0.332869  0.435573  0.904612  0.823884
    
    >>> metacsv.to_csv(df, 'mycsv.csv', attrs={'author': 'my name', 'date': '2015-12-31'})
    >>> 
    >>> df2 = metacsv.read_csv('mycsv.csv', index_col=[0])
    >>> df2
    <metacsv.core.containers.DataFrame (3, 4)>
              a         b         c         d
    0  0.558083  0.665184  0.226173  0.339905
    1  0.541712  0.835804  0.326078  0.179103
    2  0.332869  0.435573  0.904612  0.823884
    
    Attributes
        date:      2015-12-31
        author:    my name
    
    >>> metacsv.to_csv(df2, 'mycsv.csv', attrs={'author': 'new name'})
    >>> 
    >>> metacsv.read_csv('mycsv.csv', index_col=[0])
    <metacsv.core.containers.DataFrame (3, 4)>
              a         b         c         d
    0  0.558083  0.665184  0.226173  0.339905
    1  0.541712  0.835804  0.326078  0.179103
    2  0.332869  0.435573  0.904612  0.823884
    
    Attributes
        date:      2015-12-31
        author:    new name

* to_header

``to_header`` allows you to write the special attributes directly to a 
metacsv-formatted header file. The special attributes may be individually 
specified or taken from a metacsv container. The ``header_file`` argument to 
both ``read_csv`` and ``to_csv`` allow the creation of special header files 
which allow you to separate the metacsv-formatted header from the data if 
desired.

For example, say you have a table to read into pandas

.. code-block:: python

    >>> import metacsv, pandas as pd
    >>> pd.DataFrame(
        [['x',1,2,3],['y',4,5,6],['z',7,8,9]], columns=['index','a','b','c']).to_csv('mycsv.csv', index=None)
    >>> metacsv.read_csv('mycsv.csv')
    <metacsv.core.containers.DataFrame (3, 4)>
      index  a  b  c
    0     x  1  2  3
    1     y  4  5  6
    2     z  7  8  9

A separate header file can be created and used which can then be read in with the data:

.. code-block:: python

    >>> metacsv.to_header('mycsv.header', attrs={'author': 'me'}, coords='index')
    >>> metacsv.read_csv('mycsv.csv', header_file='mycsv.header')
    <metacsv.core.containers.DataFrame (3, 3)>
           a  b  c
    index
    x      1  2  3
    y      4  5  6
    z      7  8  9

    Coordinates
      * index      (index) object x, y, z
    Attributes
        author:         me


* to_xarray

``to_xarray`` returns any container or csv file as an xarray container. Table 
data (CSV files and DataFrames) will create ``xarray.Dataset`` objects, while 
Series objects will create ``xarray.DataArray`` objects. Keyword arguments 
``attrs``, ``coords``, and ``variables`` will be attached to the data before it 
is written. Any conflicts in these attributes will be updated with the arguments 
to this function.

* to_dataarray

``to_dataarray`` returns any container or csv file as an ``xarray.DataArray``. 
Table data (CSV files and DataFrames) will be stacked, with columns re-arranged 
as new ``xarray.Coordinates``. Keyword arguments ``attrs``, ``coords``, and 
``variables`` will be attached to the data before it is written. Any conflicts 
in these attributes will be updated with the arguments to this function.

* to_dataset

``to_dataarray`` returns any container or csv file as an ``xarray.DataArray``. 
Table data (CSV files and DataFrames) will be stacked, with columns re-arranged 
as new ``xarray.Coordinates``. Keyword arguments ``attrs``, ``coords``, and 
``variables`` will be attached to the data before it is written. Any conflicts 
in these attributes will be updated with the arguments to this function.

* to_pandas

``to_pandas`` strips special attributes and returns an ordinary ``Series`` or 
``DataFrame`` object.

* to_netcdf

``to_netcdf`` first converts a container or csv file to an ``xarray.Dataset`` 
using the ``to_dataset`` function, then writes the dataset to file with the
``xarray`` ``ds.to_netcdf`` method.

.. code-block:: python

    >>> metacsv.to_netcdf('mycsv.csv', 'mycsv.nc', header_file='mycsv.header')
    >>> import xarray as xr
    >>> xr.open_dataset('mycsv.nc')
    <xarray.Dataset>
    Dimensions:  (index: 3)
    Coordinates:
      * index    (index) |S1 'x' 'y' 'z'
    Data variables:
        a        (index) int64 1 4 7
        b        (index) int64 2 5 8
        c        (index) int64 3 6 9
    Attributes:
        author: me

Special attributes
-----------------------------------------------

The ``coords`` and ``variables`` attributes are keywords and are not simply 
passed to the MetaCSV object's ``attrs`` attribute.


Variables
~~~~~~~~~~~~~

Variables are attributes which apply to speicific columns or data variables. In 
MetaCSV containers, variables are displayed as a separate set of attributes. On 
conversion to ``xarray``, these attributes are assigned to variable-specific 
``attrs``:

.. code-block:: python

    >>> ds = df.to_xarray()
    >>> ds
    <xarray.Dataset>
    Dimensions:  (index: 4)
    Coordinates:
      * index    (index) int64 0 1 2 3
    Data variables:
        region   (index) object 'USA' 'USA' 'CAN' 'CAN'
        year     (index) int64 2010 2011 2010 2011
        pop      (index) float64 309.3 311.7 34.0 34.3
        gdp      (index) float64 1.36e+04 1.382e+04 1.24e+03 1.277e+03
    Attributes:
        date: 2000-12-31
        author: A Person
    
    >>> ds.pop
    <xarray.DataArray 'pop' (index: 4)>
    array([ 309.3,  311.7,   34. ,   34.3])
    Coordinates:
      * index    (index) int64 0 1 2 3
    Attributes:
        name: Population
        unit: millions

Note that at present, variables are not persistent across slicing operations.

**parse_vars**

Variables have a special argument to ``read_csv``: ``parse_vars`` allows parsing of one-line variable definitions in the format ``var: description [unit]``:

.. code-block:: python

    >>> doc = io.StringIO('''
    ---
    author: A Person
    date:   2000-12-31
    variables:
        pop: Population [millions]
        gdp: Product [2005 $Bn]
    ...
    region,year,pop,gdp
    USA,2010,309.3,13599.3
    USA,2011,311.7,13817.0
    CAN,2010,34.0,1240.0
    CAN,2011,34.3,1276.7
    ''')
    
    >>> metacsv.read_csv(doc, index_col=0, parse_vars=True)
    <metacsv.core.containers.DataFrame (4, 3)>
            year    pop      gdp
    region
    USA     2010  309.3  13599.3
    USA     2011  311.7  13817.0
    CAN     2010   34.0   1240.0
    CAN     2011   34.3   1276.7
    
    Variables
        gdp:       {u'description': 'Product', u'unit': '2005 $Bn'}
        pop:       {u'description': 'Population', u'unit': 'millions'}
    Attributes
        date:      2000-12-31
        author:    A Person

Coordinates
~~~~~~~~~~~~~

The conceptual foundation of coordinates is taken from ``xarray``, where data is 
treated as an ndarray rather than a table. If you plan to only work with the 
pandas-like features of ``metacsv``, you do not really need coordinates.

That said, specifying the ``coords`` attribute in a csv results in automatic
index handling:

.. code-block:: python

    >>> doc = io.StringIO('''
    ---
    author: A Person
    date:   2000-12-31
    variables:
        pop:
          name: Population
          unit: millions
        gdp:
          name: Product
          unit: 2005 $Bn
    coords:
        - region
        - year
    ...
    region,year,pop,gdp
    USA,2010,309.3,13599.3
    USA,2011,311.7,13817.0
    CAN,2010,34.0,1240.0
    CAN,2011,34.3,1276.7
    ''')
    
    >>> df = metacsv.read_csv(doc)
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
        gdp:       OrderedDict([('name', 'Product'), ('unit', '2005 $Bn')])
        pop:       OrderedDict([('name', 'Population'), ('unit', 'millions')])
    Attributes
        date:      2000-12-31
        author:    A Person


Coordinates become especially useful, however, when moving to ``xarray`` objects 
or ``netCDF`` files. The ``DataFrame`` above will have no trouble, as ``region`` 
and ``year`` are orthoganal:

.. code-block:: python

    >>> df.to_xarray()
    <xarray.Dataset>
    Dimensions:  (region: 2, year: 2)
    Coordinates:
      * region   (region) object 'USA' 'CAN'
      * year     (year) int64 2010 2011
    Data variables:
        pop      (region, year) float64 309.3 311.7 34.0 34.3
        gdp      (region, year) float64 1.36e+04 1.382e+04 1.24e+03 1.277e+03
    Attributes:
        date: 2000-12-31
        author: A Person

This becomes more complicated when columns in the index are not independent and 
cannot be thought of as orthogonal. In this case, you can specify ``coords`` as 
a dict-like attribute either in the CSV header or as an argument to the 
conversion method:

.. code-block:: python

    doc = io.StringIO('''
    ---
    coords:
        region:
        regname: 'region'
        continent: 'region'
        year:
    ...
    region,regname,continent,year,pop,gdp
    USA,United States,North America,2010,309.3,13599.3
    USA,United States,North America,2011,311.7,13817.0
    CAN,Canada,North America,2010,34.0,1240.0
    CAN,Canada,North America,2011,34.3,1276.7
    ''')
    
    >>> metacsv.to_xarray(doc)
    <xarray.Dataset>
    Dimensions:    (region: 2, year: 2)
    Coordinates:
      * region     (region) object 'USA' 'CAN'
      * year       (year) int64 2010 2011
        regname    (region) object 'United States' 'Canada'
        continent  (region) object 'North America' 'North America'
    Data variables:
        pop        (region, year) float64 309.3 311.7 34.0 34.3
        gdp        (region, year) float64 1.36e+04 1.382e+04 1.24e+03 1.277e+03

Note that the resulting ``Dataset`` is not indexed by the cartesian product of 
all four coordinates, but only by the base coordinates, indicated by the ``*``. 
Without first setting the ``coords`` attribute this way, the resulting data 
would have ``NaN`` values corresponding to ``(USA, Canada)`` and 
``(CAN, United States)``.


TODO
============

* Allow automatic coersion of ``xarray.Dataset`` and ``xarray.DataArray`` 
  objects to MetaCSV containers.

* Extend metacsv functionality to ``Panel`` objects

* Make ``coords`` and ``attrs`` persistent across slicing operations 
  (try ``df['pop'].to_xarray()`` from above example and watch it 
  fail...)

* Improve hooks between ``pandas`` and ``metacsv``:

  - update ``coord`` names on ``df.index.names`` assignment
  - update ``coords`` on stack/unstack
  - update ``coords`` on 

* Improve parser to automatically strip trailing commas and other excel relics

* Enable ``read_csv(engine='C')``... this currently does not work.

* Handle attributes indexed by coord/variable names --> assign to 
  coord/variable-specific ``attrs``

* Let's start an issue tracker and get rid of this section!

* Should we rethink "special attribute," naming e.g. coords? Maybe these should 
  have some special prefix like ``_coords`` when included in yaml headers to 
  avoid confusion with other generic attributes...

* Allow attribute assertions (e.g. ``version='>1.6.0'``) in ``read_csv`` call

* Improve test coverage

* Improve documentation & build readthedocs page



Feature Requests
==================
* Create syntax for ``multi-csv`` --> ``Panel`` or combining using filename 
  regex 
* Eventually? allow for on-disk manipulation of many/large files with 
  dask/xarray 
* Eventually? add xml, SQL, other structured syntax language conversions


.. _BSD: http://opensource.org/licenses/BSD-3-Clause
.. _Documentation: http://metacsv.readthedocs.org/en/latest/
.. _API: http://metacsv.readthedocs.org/en/latest/api.html
