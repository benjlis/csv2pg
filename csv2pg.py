"""csv2pg -  Utility for loading a CSV file into PostgreSQL."""

import argparse
import csv
import magic

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
parser.add_argument('-o', '--optcp',
                    help='copy command options')
args = parser.parse_args()


def convert_utf8(filename, filetype):
    """Convert filename to UTF-8 without BOM."""
    print("File {} appears to be in {} format.".format(filename, filetype))
    print("Converting to utf-8 without bom.")
    if filetype == 'utf-8':             # to handle BOM
        filetype = 'utf-8-sig'
    with open(filename, "rb") as fin:
        text = fin.read()
    text = text.decode(filetype).encode('utf-8')
    utf8_out = 'csv2pg-' + filename
    with open(utf8_out, "wb") as fou:
        fou.write(text)
    print("Converted file: {}".format(utf8_out))
    return utf8_out


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
    ddl = ddl[:-2] + "\n);\n"
    return ddl


def gen_copy_cmd(tabname, colnames, filename, optcp):
    """Generate the copy command for the CSV file."""
    ddl = "\copy {}(".format(tabname)
    for c in colnames:
        ddl = ddl + "{}, ".format(c)
    ddl = ddl[:-2] + ") from '{}' {};\n".format(filename, optcp)
    return ddl


table_name = args.table or get_table_name(args.filename)
# determine the file type and generate a UTF-8 version of file if necessary
f = magic.Magic(mime_encoding="True")
try:
    file_format = f.from_file(args.filename)
except FileNotFoundError:
    print("File {} not found".format(args.filename))
    raise SystemExit
# TBD - handle for Postgres DBs where character set is not UTF-8
# TBD - better testing for BOM, better use of space.
csvfilename = convert_utf8(args.filename, file_format)
csvfile = open(csvfilename, newline='')
csvreader = csv.reader(csvfile)
csvheader = csvreader.__next__()                    # read the header
create_table = gen_table_ddl(table_name, args.pk, csvheader)
copy_opts = args.optcp or "DELIMITER ',' CSV HEADER"
copy_cmd = gen_copy_cmd(table_name, csvheader, csvfilename, copy_opts)
# write the DDL to a file
ddl_file_name = "{}.sql".format(args.ddl or table_name)
ddl_file = open(ddl_file_name, "w+")
ddl_file.write(create_table)
ddl_file.write(copy_cmd)
print("Generated SQL file: {}".format(ddl_file_name))
