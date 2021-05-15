#  xml2csv - Another xml to csv converter.
#     Copyright (C) 2021 J. Férard <https://github.com/jferard>
#
#  This file is part of xml2csv.
#
#  xml2csv is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  xml2csv is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import ast
import csv
import sys
import xml.etree.ElementTree as ET

from dom import ProductFlattener
from sax import NoProductFlattener


def xml2csv(filename, out=sys.stdout, short_names=False, product=True,
            aliases=None, number_cols=True, **kwargs):
    if "dialect" in kwargs:
        writer = csv.writer(out, kwargs["dialect"])
    else:
        writer = csv.writer(out, **kwargs)

    if product:
        tree = ET.parse(filename)
        flattener = ProductFlattener(tree.getroot(), short_names=short_names,
                                     number_cols=number_cols, aliases=aliases)
        for r in flattener.flatten():
            writer.writerow(r)
    elif aliases:
        raise ValueError("Can ony have aliases with product")
    else:
        flattener = NoProductFlattener(filename, short_names=short_names,
                                       number_cols=number_cols)
        flattener.flatten(writer)


class ParseDictAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, ast.literal_eval(values))


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Convert an XML file to a CSV file.')
    parser.add_argument('filename', help='a file to convert')
    parser.add_argument('-s', '--short-names',
                        help='use short names for columns', action='store_true')
    parser.add_argument('-a', '--aliases', default=None,
                        help='set aliases as a python dictionary',
                        action=ParseDictAction)
    parser.add_argument('-p', '--no-product',
                        help="don't use cartesian product", action='store_true')
    parser.add_argument('-n', '--no-numbers',
                        help="don't create number columns for tags", action='store_true')
    return parser
