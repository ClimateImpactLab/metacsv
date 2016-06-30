
from collections import OrderedDict
from .yaml_tools import ordered_dump
from .._compat import string_types, has_iterkeys, iterkeys


def _header_to_file_object(fp, attrs=None, coords=None, variables=None):

    attr_dict = OrderedDict()

    if attrs != None:
        attr_dict.update(attrs)

    if coords != None:
        attr_dict.update({'coords': coords})

    if variables != None:
        attr_dict.update({'variables': variables})

    if len(attr_dict) > 0:
        fp.write('---\n')
        fp.write(ordered_dump(
            attr_dict, default_flow_style=False, allow_unicode=True))
        fp.write('...\n')

def _container_to_csv_object(container, fp, *args, **kwargs):
    container.pandas_parent.to_csv(container, fp, *args, **kwargs)

def metacsv_to_csv(container, fp, *args, **kwargs):
    if isinstance(fp, string_types):
        with open(fp, 'w+') as fp2:
            _header_to_file_object(fp2, attrs=container.attrs, coords=container.coords, variables=container.variables)
            _container_to_csv_object(container, fp2, *args, **kwargs)
    else:
        _header_to_file_object(fp, attrs=container.attrs, coords=container.coords, variables=container.variables)
        _container_to_csv_object(container, fp, *args, **kwargs)
