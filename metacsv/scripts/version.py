
from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals
)

import metacsv, argparse, sys

def get_version(readfile):
	df = metacsv.read_csv(readfile)
	version = df.attrs.get('version', None)
	return version


def get_parser():
	parser = argparse.ArgumentParser('Get the version number from a MetaCSV-formatted CSV file')
	parser.add_argument('readfile', help='Input CSV file to read')

	return parser

def main():
	parser = get_parser()
	args = parser.parse_args()

	version = get_version(args.readfile)

	if version is None:
		print('No version found', file=sys.stderr)

	else:
		print(version)

if __name__ == "__main__":
	main()
