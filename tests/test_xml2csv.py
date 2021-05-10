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

import unittest

import xml.etree.ElementTree as ET
from io import StringIO

from src.xml2csv import Flattener, get_parser


class TestXML2CSV(unittest.TestCase):
    def test_simple(self):
        root = ET.fromstring("""
<row>
    <cell style="s">A1</cell>
    <cell>B1</cell>
</row>
        """)
        flattener = Flattener(root)
        self.assertEqual(
            [['row.#num', 'row.cell.#num', 'row.cell.@style', 'row.cell._text'],
             [0, 0, 's', 'A1'],
             [0, 1, None, 'B1']], list(flattener.flatten()))

    def test_two_rows(self):
        root = ET.fromstring("""
    <data n="1" m="2">
        <row>
            <rowinfo type="long"/> 
            <cell style="s">A1</cell>
            <cell>B1</cell>
        </row>
        <row>
            <cell otherstyle="s2">A2</cell>
            <cell>B2</cell>
        </row>
    </data>""")
        flattener = Flattener(root)
        self.assertEqual(
            [['data.#num',
              'data.@n',
              'data.@m',
              'data.row.#num',
              'data.row.rowinfo.#num',
              'data.row.rowinfo.@type',
              'data.row.cell.#num',
              'data.row.cell.@style',
              'data.row.cell._text',
              'data.row.cell.@otherstyle'],
             [0, '1', '2', 0, 0, 'long', 0, 's', 'A1', None],
             [0, '1', '2', 0, 0, 'long', 1, None, 'B1', None],
             [0, '1', '2', 1, None, None, 0, None, 'A2', 's2'],
             [0, '1', '2', 1, None, None, 1, None, 'B2', None]],
            list(flattener.flatten()))

    def test_product(self):
        root = ET.fromstring("""<row>
    <column style="s" />
    <column style="t" />
    <cell>A2</cell>
    <cell>B2</cell>
</row>""")
        flattener = Flattener(root)
        self.assertEqual(
            [['row.#num',
              'row.column.#num',
              'row.column.@style',
              'row.cell.#num',
              'row.cell._text'],
             [0, 0, 's', 0, 'A2'],
             [0, 0, 's', 1, 'B2'],
             [0, 1, 't', 0, 'A2'],
             [0, 1, 't', 1, 'B2']], list(flattener.flatten()))

    def test_no_product(self):
        root = ET.fromstring("""
        <row>
            <cell>A1</cell>
            <cell cover="3">B1</cell>
            <covered-cell>C1</covered-cell>
            <covered-cell>D1</covered-cell>
        </row>
                """)
        flattener = Flattener(root, aliases={"covered-cell": "cell"})
        self.assertEqual(
            [['row.#num',
              'row.cell.#num',
              'row.cell._text',
              'row.cell.@cover',
              'row.covered-cell.#num',
              'row.covered-cell._text'],
             [0, 0, 'A1', None, None, None],
             [0, 1, 'B1', '3', None, None],
             [0, None, None, None, 0, 'C1'],
             [0, None, None, None, 1, 'D1']], list(flattener.flatten()))

    def test_elementree_module_example(self):
        root = ET.fromstring("""<?xml version="1.0"?>
        <data>
            <country name="Liechtenstein">
                <rank>1</rank>
                <year>2008</year>
                <gdppc>141100</gdppc>
                <neighbor name="Austria" direction="E"/>
                <neighbor name="Switzerland" direction="W"/>
            </country>
            <country name="Singapore">
                <rank>4</rank>
                <year>2011</year>
                <gdppc>59900</gdppc>
                <neighbor name="Malaysia" direction="N"/>
            </country>
            <country name="Panama">
                <rank>68</rank>
                <year>2011</year>
                <gdppc>13600</gdppc>
                <neighbor name="Costa Rica" direction="W"/>
                <neighbor name="Colombia" direction="E"/>
            </country>
        </data>""")
        flattener = Flattener(root)
        self.assertEqual(
            [['data.#num',
              'data.country.#num',
              'data.country.@name',
              'data.country.rank.#num',
              'data.country.rank._text',
              'data.country.year.#num',
              'data.country.year._text',
              'data.country.gdppc.#num',
              'data.country.gdppc._text',
              'data.country.neighbor.#num',
              'data.country.neighbor.@name',
              'data.country.neighbor.@direction'],
             [0, 0, 'Liechtenstein', 0, '1', 0, '2008', 0, '141100', 0,
              'Austria', 'E'],
             [0, 0, 'Liechtenstein', 0, '1', 0, '2008', 0, '141100', 1,
              'Switzerland', 'W'],
             [0, 1, 'Singapore', 0, '4', 0, '2011', 0, '59900', 0, 'Malaysia',
              'N'],
             [0, 2, 'Panama', 0, '68', 0, '2011', 0, '13600', 0, 'Costa Rica',
              'W'],
             [0, 2, 'Panama', 0, '68', 0, '2011', 0, '13600', 1, 'Colombia',
              'E']],
            list(flattener.flatten()))

    def test_elementree_module_example_short_names(self):
        root = ET.fromstring("""<?xml version="1.0"?>
        <data>
            <country name="Liechtenstein">
                <rank>1</rank>
                <year>2008</year>
                <gdppc>141100</gdppc>
                <neighbor name="Austria" direction="E"/>
                <neighbor name="Switzerland" direction="W"/>
            </country>
            <country name="Singapore">
                <rank>4</rank>
                <year>2011</year>
                <gdppc>59900</gdppc>
                <neighbor name="Malaysia" direction="N"/>
            </country>
            <country name="Panama">
                <rank>68</rank>
                <year>2011</year>
                <gdppc>13600</gdppc>
                <neighbor name="Costa Rica" direction="W"/>
                <neighbor name="Colombia" direction="E"/>
            </country>
        </data>""")
        flattener = Flattener(root, short_names=True)
        self.assertEqual(
            [['data.#num',
              'country.#num',
              'country.@name',
              'rank.#num',
              'rank._text',
              'year.#num',
              'year._text',
              'gdppc.#num',
              'gdppc._text',
              'neighbor.#num',
              'neighbor.@name',
              'neighbor.@direction'],
             [0, 0, 'Liechtenstein', 0, '1', 0, '2008', 0, '141100', 0,
              'Austria', 'E'],
             [0, 0, 'Liechtenstein', 0, '1', 0, '2008', 0, '141100', 1,
              'Switzerland', 'W'],
             [0, 1, 'Singapore', 0, '4', 0, '2011', 0, '59900', 0, 'Malaysia',
              'N'],
             [0, 2, 'Panama', 0, '68', 0, '2011', 0, '13600', 0, 'Costa Rica',
              'W'],
             [0, 2, 'Panama', 0, '68', 0, '2011', 0, '13600', 1, 'Colombia',
              'E']],
            list(flattener.flatten()))


class TestParser(unittest.TestCase):
    def test_help(self):
        s = StringIO()
        get_parser().print_help(s)
        self.assertEqual(['',
                          'Convert an XML file to a CSV file.',
                          '',
                          'positional arguments:',
                          '  filename              a file to convert',
                          '',
                          'optional arguments:',
                          '  -h, --help            show this help message and exit',
                          '  -s, --shortnames      use short names for columns',
                          '  -a ALIASES, --aliases ALIASES',
                          '                        set aliases as a python dictionary',
                          ''], s.getvalue().split("\n")[1:])

    def test_filename(self):
        args = get_parser().parse_args(["f1"])
        self.assertEqual("f1", args.filename)
        self.assertFalse(args.shortnames)
        self.assertIsNone(args.aliases)

    def test_shortnames(self):
        args = get_parser().parse_args(["-s", "f1"])
        self.assertEqual("f1", args.filename)
        self.assertTrue(args.shortnames)
        self.assertIsNone(args.aliases)

    def test_aliases(self):
        args = get_parser().parse_args(["-a", "{'other_cell':'cell'}", "f1"])
        self.assertEqual("f1", args.filename)
        self.assertFalse(args.shortnames)
        self.assertEqual({'other_cell': 'cell'}, args.aliases)


if __name__ == '__main__':
    unittest.main()
