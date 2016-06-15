
from __future__ import absolute_import, print_function
import metacsv
import argparse, os

def to_netcdf(readfile, writefile=None, *args, **kwargs):
	if writefile is None:
		writefile = os.path.splitext(readfile)[0] + '.nc'

	metacsv.read_csv(readfile, *args, **kwargs).to_xarray().to_netcdf(writefile)

def get_parser():
	parser = argparse.ArgumentParser('Convert MetaCSV-compliant files to other file types')
	parser.add_argument('action', help='type of file to be written (netcdf, csv)')
	parser.add_argument('readfile', help='Input CSV file to read')
	parser.add_argument('writefile', nargs='?', default=None, help='Output file to read')
	parser.add_argument('--header', nargs='?', default=None, help='Header file for CSV read file')

	return parser

def main():
	parser = get_parser()
	args = parser.parse_args()
	
	if args.action.lower() == 'netcdf':
		to_netcdf(args.readfile, args.writefile, header_file=args.header)

	elif args.action.lower() == 'csv':
		to_csv(args.readfile, args.writefile, header_file=args.header)

	else:
		parser.print_help()

if __name__ == "__main__":
	main()