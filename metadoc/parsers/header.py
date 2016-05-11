
import yaml, pandas as pd, re
from .._compat import string_types, StringIO

from metadoc.core.containers import Series, DataFrame, Panel

def find_yaml_break(line):
	return re.search(r'^\s*-{3,}\s*$', line) is not None

def _parse_headered_data(fp, *args, **kwargs):

	# Check for a yaml parse break at the top of the file
	# if there is not one, go back to the top and read like a
	# normal CSV
  loc = fp.tell()

  nextline = ''

  while re.search(r'^\s*$', nextline):
  	nextline = next(fp)

  if not find_yaml_break(nextline):
  	print('returning!!!')
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

	if isinstance(string_or_buffer, string_types):
		with open(string_or_buffer, 'r') as fp:
			header, data = _parse_headered_data(fp, *args, **kwargs)

	else:
		header, data = _parse_headered_data(string_or_buffer, *args, **kwargs)

	if kwargs.get('squeeze', False):
		if len(data.shape) == 1:
			return Series(data, attrs=header)

	return DataFrame(data, attrs=header)

	