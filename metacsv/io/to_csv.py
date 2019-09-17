
from collections import OrderedDict
from .yaml_tools import ordered_dump
from .._compat import string_types, has_iterkeys, iterkeys, text_type, text_to_native


def _header_to_file_object(fp, attrs=None, coords=None, variables=None):

    attr_dict = OrderedDict()

    if attrs != None:
        attr_dict.update(attrs._data)

    if coords != None:
        attr_dict.update({'coords': coords._coords})

    if variables != None:
        attr_dict.update({'variables': variables._data})

    if len(attr_dict) > 0:
        fp.write(text_to_native(('---\n'), 'utf-8'))
        fp.write(text_to_native(ordered_dump(
            attr_dict, default_flow_style=False, allow_unicode=True), 'utf-8'))
        fp.write(text_to_native(('...\n'), 'utf-8'))

def _container_to_csv_object(container, fp, *args, **kwargs):
    encoding = kwargs.pop('encoding', 'utf-8')
    container.pandas_parent.to_csv(container.to_pandas(), fp, *args, encoding=encoding, **kwargs)

def metacsv_to_csv(container, fp, header_file=None, *args, **kwargs):
    separate_header = False

    if (header_file is not None) and (header_file != fp):
        separate_header = True

    if separate_header:
        metacsv_to_header(header_file, attrs=container.attrs, coords=container.coords, variables=container.variables)

    if isinstance(fp, string_types):
        with open(text_type(fp), 'w+') as fp2:
            if not separate_header:
                _header_to_file_object(fp2, attrs=container.attrs, coords=container.coords, variables=container.variables)
            _container_to_csv_object(container, fp2, *args, **kwargs)
    else:
        if not separate_header:
            _header_to_file_object(fp, attrs=container.attrs, coords=container.coords, variables=container.variables)
        _container_to_csv_object(container, fp, *args, **kwargs)

def metacsv_to_header(fp, attrs=None, coords=None, variables=None):
    if isinstance(fp, string_types):
        with open(text_type(fp), 'w+') as fp2:
            _header_to_file_object(fp2, attrs=attrs, coords=coords, variables=variables)
    else:
        _header_to_file_object(fp, attrs=attrs, coords=coords, variables=variables)
