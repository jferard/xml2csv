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
import xml.etree.ElementTree as ET

from src.xml2csv import Flattener


class TestAlgorithm(unittest.TestCase):
    def test1(self):
        root = ET.fromstring("""<root>
    <foo>foo1</foo>
    <bar>bar1</bar>
    <baz>baz1</baz>
</root>""")
        flattener = Flattener(root, short_names=True)
        self.assertEqual(
            [['root.#num',
              'foo.#num',
              'foo._text',
              'bar.#num',
              'bar._text',
              'baz.#num',
              'baz._text'],
             [0, 0, 'foo1', 0, 'bar1', 0, 'baz1']], list(flattener.flatten()))

    def test2(self):
        root = ET.fromstring("""<root>
    <foo>foo1</foo>
    <foo>foo2</foo>
    <bar>bar1</bar>
</root>""")
        flattener = Flattener(root, short_names=True)
        self.assertEqual(
            [['root.#num', 'foo.#num', 'foo._text', 'bar.#num', 'bar._text'],
             [0, 0, 'foo1', 0, 'bar1'],
             [0, 1, 'foo2', 0, 'bar1']], list(flattener.flatten()))

    def test3(self):
        root = ET.fromstring("""<root>
    <foo>foo1</foo>
    <foo>foo2</foo>
    <bar>bar1</bar>
    <bar>bar2</bar>
</root>""")
        flattener = Flattener(root, short_names=True)
        self.assertEqual(
            [['root.#num', 'foo.#num', 'foo._text', 'bar.#num', 'bar._text'],
             [0, 0, 'foo1', 0, 'bar1'],
             [0, 0, 'foo1', 1, 'bar2'],
             [0, 1, 'foo2', 0, 'bar1'],
             [0, 1, 'foo2', 1, 'bar2']], list(flattener.flatten()))

    def test4(self):
        root = ET.fromstring("""<root>
    <foo>foo1</foo>
    <foo>foo2</foo>
    <bar>bar1</bar>
</root>""")
        flattener = Flattener(root, short_names=True, aliases={'bar': 'foo'})
        self.assertEqual(
            [['root.#num', 'foo.#num', 'foo._text', 'bar.#num', 'bar._text'],
             [0, 0, 'foo1', None, None],
             [0, 1, 'foo2', None, None],
             [0, None, None, 0, 'bar1']], list(flattener.flatten()))

    def test5(self):
        root = ET.fromstring("""<root>
    <foo>
        <bar>bar1</bar>
        <bar>bar2</bar>
        <baz>baz1</baz>
    </foo>
    <foo>
        <baz>baz2</baz>
    </foo>
</root>""")
        flattener = Flattener(root, short_names=True)
        self.assertEqual(
            [['root.#num',
              'foo1.#num',
              'bar.#num',
              'bar._text',
              'baz.#num',
              'baz._text',
              'foo2.#num',
              'baz.#num',
              'baz._text'],
             [0, 0, 0, 'bar1', 0, 'baz1', 0, 0, 'baz2'],
             [0, 0, 1, 'bar2', 0, 'baz1', 0, 0, 'baz2']], list(flattener.flatten()))


if __name__ == "__main__":
    unittest.main()