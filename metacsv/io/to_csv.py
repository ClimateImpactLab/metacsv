
from collections import OrderedDict
from .yaml_tools import ordered_dump
from .._compat import string_types, has_iterkeys, iterkeys


def _to_csv_object(container, fp, *args, **kwargs):
  attr_dict = OrderedDict()
  attr_dict.update(dict(container.attrs))

  if container.coords != None:
    attr_dict.update({'coords': dict(container.coords.items())})

  if hasattr(container, 'variables') and container.variables != None:
    attr_dict.update({'variables': dict(container.variables.items())})

  if len(attr_dict) > 0:
    fp.write('---\n')
    fp.write(ordered_dump(attr_dict, default_flow_style=False, allow_unicode=True))
    fp.write('...\n')
  container.pandas_parent.to_csv(container, fp, *args, **kwargs)

def metacsv_to_csv(container, fp, *args, **kwargs):
  if isinstance(fp, string_types):
    with open(fp, 'w+') as fp2:
      _to_csv_object(container, fp2, *args, **kwargs)
  else:
    _to_csv_object(container, fp, *args, **kwargs)