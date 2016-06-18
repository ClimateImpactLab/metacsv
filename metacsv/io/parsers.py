
import pandas as pd, re
from .yaml_tools import ordered_load
from .._compat import string_types
from ..core.internals import Container, Variables

from metacsv.core.containers import Series, DataFrame, Panel

def find_yaml_start(line):
  return re.search(r'^\s*-{3,}\s*$', line) is not None

def find_yaml_stop(line):
  return re.search(r'^\s*\.{3,}\s*$', line) is not None

def _parse_headered_data(fp, *args, **kwargs):

  # Check for a yaml parse break at the top of the file
  # if there is not one, go back to the top and read like a
  # normal CSV
  loc = fp.tell()

  nextline = ''

  while re.search(r'^[\s\n\r]*$', nextline):
    nextline = next(fp)

  if not find_yaml_start(nextline):
    fp.seek(loc)
    return {}, pd.read_csv(fp, *args, **kwargs)
  
  yaml_text = ''
  this_line = ''

  while not find_yaml_stop(this_line):
    yaml_text += '\n' + this_line.rstrip('\n')
    this_line = next(fp)

  header = ordered_load(yaml_text)
  data = pd.read_csv(fp, *args, **kwargs)

  return header, data


def read_csv(string_or_buffer, header_file=None, parse_vars=False, *args, **kwargs):
  
  kwargs = dict(kwargs)

  squeeze = kwargs.get('squeeze', False)

  # set defaults
  engine = kwargs.pop('engine', 'python')
  kwargs['engine'] = engine
  
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

  kwargs.update({'attrs': header})
  args, kwargs, special = Container.strip_special_attributes(args, kwargs)

  if parse_vars:
    if 'variables' in special:
      for key, var in special['variables'].items():
        special['variables'][key] = Variables.parse_string_var(var)

  if squeeze:
    if len(data.shape) == 1:
      return Series(data, **special)

  df = DataFrame(data, **special)

  if squeeze and df.shape[1] == 1:
    return Series(df[df.columns[0]], **special)
  else:
    return df

  