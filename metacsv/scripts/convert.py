
from __future__ import (
    absolute_import,
    division, print_function, with_statement,
    unicode_literals
)

import metacsv
import argparse
import os


def _to_netcdf(fp, writefile=None, *args, **kwargs):
    if writefile is None:
        writefile = os.path.splitext(readfile)[0] + '.nc'

    metacsv.to_netcdf(fp, writefile, *args, **kwargs)

def _to_csv(fp, writefile=None, *args, **kwargs):
    if writefile is None:
        writefile = os.path.splitext(readfile)[0] + '.csv'

    metacsv.to_csv(fp, writefile, *args, **kwargs)


def get_parser():
    parser = argparse.ArgumentParser(
        'Convert MetaCSV-compliant files to other file types')
    parser.add_argument(
        'action', help='type of file to be written (netcdf, csv)')
    parser.add_argument('readfile', help='Input CSV file to read')
    parser.add_argument('writefile', nargs='?',
                        default=None, help='Output file to read')
    parser.add_argument('--header', nargs='?', default=None,
                        help='Header file for CSV read file')

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.action.lower() == 'netcdf':
        _to_netcdf(args.readfile, args.writefile, header_file=args.header)

    elif args.action.lower() == 'csv':
        _to_csv(args.readfile, args.writefile, header_file=args.header)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
