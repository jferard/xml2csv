#  xml2csv - Another xml2csv converter.
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
from io import StringIO

from xml2csv.sax import NoProductFlattener


class MockWriter:
    def __init__(self):
        self.rows = []

    def writerow(self, row):
        self.rows.append(row)


class TestNoProductAlgorithm(unittest.TestCase):
    def test1(self):
        self._flatten_is_equal("""<root>
    <foo>foo1</foo>
    <bar>bar1</bar>
    <baz>baz1</baz>
</root>""", [['root.#num',
              'foo.#num',
              'foo.^text',
              'bar.#num',
              'bar.^text',
              'baz.#num',
              'baz.^text'],
             [0, 0, 'foo1', 0, 'bar1', 0, 'baz1']])

    def _flatten_is_equal(self, xml, expected):
        source = StringIO(xml)
        writer = MockWriter()
        flattener = NoProductFlattener(source, short_names=True,
                                       number_cols=True)
        flattener.flatten(writer)
        self.assertEqual(expected, writer.rows)

    def test2(self):
        self._flatten_is_equal("""<root>
    <foo>foo1</foo>
    <foo>foo2</foo>
    <bar>bar1</bar>
</root>""", [['root.#num', 'foo.#num', 'foo.^text', 'bar.#num', 'bar.^text'],
             [0, 0, 'foo1', 0, 'bar1'],
             [0, 1, 'foo2', 0, 'bar1']])

    def test3(self):
        self._flatten_is_equal("""<root>
    <foo>foo1</foo>
    <foo>foo2</foo>
    <bar>bar1</bar>
    <bar>bar2</bar>
</root>""", [['root.#num', 'foo.#num', 'foo.^text', 'bar.#num', 'bar.^text'],
             [0, 0, 'foo1', '', ''],
             [0, 1, 'foo2', '', ''],
             [0, '', '', 0, 'bar1'],
             [0, '', '', 1, 'bar2']])

    def test4(self):
        self._flatten_is_equal("""<root>
    <foo>foo1</foo>
    <foo>foo2</foo>
    <bar>bar1</bar>
</root>""", [['root.#num', 'foo.#num', 'foo.^text', 'bar.#num', 'bar.^text'],
             [0, 0, 'foo1', 0, 'bar1'],
             [0, 1, 'foo2', 0, 'bar1']])

    def test5(self):
        self._flatten_is_equal("""<root>
    <foo>
        <bar>bar1</bar>
        <bar>bar2</bar>
        <baz>baz1</baz>
    </foo>
    <foo>
        <baz>baz2</baz>
    </foo>
</root>""", [['root.#num',
              'foo.#num',
              'bar.#num',
              'bar.^text',
              'baz.#num',
              'baz.^text'],
             [0, 0, 0, 'bar1', 0, 'baz1'],
             [0, 0, 1, 'bar2', 0, 'baz1'],
             [0, 1, '', '', 0, 'baz2']])

    def test6(self):
        self._flatten_is_equal("""<root r="root">
    <foo attr="f">
        <bar>bar1</bar>
        <bar>bar2</bar>
        <baz attr2="z">baz1</baz>
    </foo>
    <foo>
        <baz>baz2</baz>
        <bat>
            <baw>1</baw>
            <baw>2</baw>
        </bat>
    </foo>
</root>""", [['root.#num',
              'root.@r',
              'foo.#num',
              'foo.@attr',
              'bar.#num',
              'bar.^text',
              'baz.#num',
              'baz.@attr2',
              'baz.^text',
              'bat.#num',
              'baw.#num',
              'baw.^text'],
             [0, 'root', 0, 'f', 0, 'bar1', 0, 'z', 'baz1', '', '', ''],
             [0, 'root', 0, 'f', 1, 'bar2', 0, 'z', 'baz1', '', '', ''],
             [0, 'root', 1, '', '', '', '', '', '', 0, 0, '1'],
             [0, 'root', 1, '', '', '', '', '', '', 0, 1, '2'],
             [0, 'root', 1, '', '', '', 0, '', 'baz2', '', '', '']])
