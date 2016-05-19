
import yaml, pandas as pd, re
from .._compat import string_types

from metacsv.core.containers import Series, DataFrame, Panel

def find_yaml_break(line):
  return re.search(r'^\s*-{3,}\s*$', line) is not None

def _parse_headered_data(fp, *args, **kwargs):

  # Check for a yaml parse break at the top of the file
  # if there is not one, go back to the top and read like a
  # normal CSV
  loc = fp.tell()

  nextline = ''

  while re.search(r'^[\s\n\r]*$', nextline):
    nextline = next(fp)

  if not find_yaml_break(nextline):
    fp.seek(loc)
    return {}, pd.read_csv(fp, *args, **kwargs)
  
  yaml_text = ''
  this_line = ''

  while not find_yaml_break(this_line):
    yaml_text += '\n' + this_line
    this_line = next(fp)

  header = yaml.load(yaml_text)
  data = pd.read_csv(fp, *args, **kwargs)

  return header, data


def read_csv(string_or_buffer, *args, **kwargs):

  kwargs = dict(kwargs)

  # set defaults
  engine = kwargs.pop('engine', 'python')
  kwargs['engine'] = engine
  
  header_file = kwargs.pop('header_file', None)

  header = {}

  if isinstance(header_file, string_types):
    with open(header_file, 'r') as hf:
      header = yaml.load(hf.read())

  elif header_file is not None:
    header = yaml.load(hf.read())

  if isinstance(string_or_buffer, string_types):
    with open(string_or_buffer, 'r') as fp:
      _header, data = _parse_headered_data(fp, *args, **kwargs)

  else:
    _header, data = _parse_headered_data(string_or_buffer, *args, **kwargs)

  header.update(_header)

  if kwargs.get('squeeze', False):
    if len(data.shape) == 1:
      return Series(data, attrs=header)

  df = DataFrame(data, attrs=header)

  squeeze = kwargs.get('squeeze', False)
  if squeeze and df.shape[1] == 1:
    return Series(df[df.columns[0]], attrs=header, coords=df.coords)
  else:
    return df

  