"""csv2pg -  Utility for loading a CSV file into PostgreSQL."""

import argparse
import csv

# process command line arguments
parser = argparse.ArgumentParser(description='Loads a CSV file into \
                                 PostgresSQL.')
parser.add_argument('filename',
                    help='CSV file to be loaded into PostgreSQL table')
parser.add_argument('-t', '--table',
                    help='table where the CSV file is copied')
parser.add_argument('-d', '--ddl',
                    help='filename of create table statement')
parser.add_argument('-p', '--pk',
                    help='system generated primary key column')
args = parser.parse_args()


def get_table_name(filename):
    """Extract the name component from the filename."""
    try:
        loc = filename.index('.')
        return filename[:loc]
    except ValueError:
        return filename


def gen_table_ddl(tabname, pkcol, colnames):
    """Generate the DDL for the PG table version of the CVS file."""
    ddl = "create table {} (\n".format(tabname)
    if pkcol:
        ddl = ddl + "\t {} \t serial,\n".format(pkcol)
    for c in colnames:
        ddl = ddl + "\t {} \t text,\n".format(c)
    ddl = ddl[:-2] + "\n);"
    return(ddl)


table_name = args.table or get_table_name(args.filename)
# open the CSV file for reading
try:
    csvfile = open(args.filename, newline='')
    csvreader = csv.reader(csvfile)
except FileNotFoundError:
    print("File {} not found".format(args.filename))
    raise SystemExit
# read the header
# iconv -f ISO-8859-1 -t UTF-8 X.csv > X_utf8.csv
try:
    create_table = gen_table_ddl(table_name, args.pk, csvreader.__next__())
except UnicodeDecodeError:
    print("File {} must be UTF-8 encoded. Try iconv.".format(args.filename))
    raise SystemExit
# write the DDL to a file
ddl_file = open("{}.sql".format(args.ddl or table_name), "w+")
ddl_file.write(create_table)
