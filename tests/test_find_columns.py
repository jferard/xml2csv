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

from xml2csv import sax, dom


class TestColumnsFinder(unittest.TestCase):
    def test_no_numbers(self):
        xml = """<root r="root">
            <foo attr="f">
                <bar>bar1</bar>
                <bar c="1">bar2</bar>
                <baz attr2="z">baz1</baz>
            </foo>
            <foo>
                <bar d="2">bar2</bar>
                <baz>baz2</baz>
                <bat>
                    <baw>1</baw>
                    <baw>2</baw>
                </bat>
            </foo>
        </root>"""
        for find_columns in sax.find_columns, dom.find_columns:
            columns = find_columns(StringIO(xml))
            self.assertEqual([('root', '@r'),
                              ('root', 'foo', '@attr'),
                              ('root', 'foo', 'bar', '@c'),
                              ('root', 'foo', 'bar', '@d'),
                              ('root', 'foo', 'bar', '^text'),
                              ('root', 'foo', 'baz', '@attr2'),
                              ('root', 'foo', 'baz', '^text'),
                              ('root', 'foo', 'bat', 'baw', '^text')],
                             columns)

    def test_numbers(self):
        xml = """<root r="root">
            <foo attr="f">
                <bar>bar1</bar>
                <bar c="1">bar2</bar>
                <baz attr2="z">baz1</baz>
            </foo>
            <foo>
                <bar d="2">bar2</bar>
                <baz>baz2</baz>
                <bat>
                    <baw>1</baw>
                    <baw>2</baw>
                </bat>
            </foo>
        </root>"""
        for find_columns in sax.find_columns, dom.find_columns:
            columns = find_columns(StringIO(xml), True)
            self.assertEqual([('root', '#num'),
                              ('root', '@r'),
                              ('root', 'foo', '#num'),
                              ('root', 'foo', '@attr'),
                              ('root', 'foo', 'bar', '#num'),
                              ('root', 'foo', 'bar', '@c'),
                              ('root', 'foo', 'bar', '@d'),
                              ('root', 'foo', 'bar', '^text'),
                              ('root', 'foo', 'baz', '#num'),
                              ('root', 'foo', 'baz', '@attr2'),
                              ('root', 'foo', 'baz', '^text'),
                              ('root', 'foo', 'bat', '#num'),
                              ('root', 'foo', 'bat', 'baw', '#num'),
                              ('root', 'foo', 'bat', 'baw', '^text')],
                             columns)
