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
import collections
import csv
import itertools
import sys
import xml.etree.ElementTree as ET
from typing import List, Tuple, Union, Dict, Mapping
from xml.etree.ElementTree import Element

Row = List[Tuple[str, Union[int, str]]]
Path = Tuple[str, ...]
RowDict = Dict[Path, Union[int, str]]


class Flattener:
    def __init__(self, root: ET.Element, short_names: bool = False,
                 aliases: Mapping[str, str] = None):
        self._root = root
        self._short_names = short_names
        self._aliases = {} if aliases is None else aliases
        self.row_dicts_by_element: Dict[ET.Element, List[RowDict]] = {}
        self.attrs_by_element: Dict[ET.Element, RowDict] = {}
        self._nodes = []

    def flatten(self):
        columns = list(self._find_columns())
        bottom_up_nodes = self._find_non_terminal_and_order_bottom_up()
        self._flatten(bottom_up_nodes)
        if self._short_names:
            yield [".".join(c[-2:]) for c in columns]
        else:
            yield [".".join(c) for c in columns]

        for row_dict in self.row_dicts_by_element[self._root]:
            yield [row_dict.get(col) for col in columns]

    def _find_columns(self):
        subtree_by_tag = collections.OrderedDict()
        stack = [((self._root.tag,), (self._root))]
        while stack:
            path, n = stack.pop()
            cur = subtree_by_tag
            for p in path:
                cur = cur.setdefault(p, {})
            if n is not None:
                for c in reversed(list(n)):
                    stack.append((path + (c.tag,), c))
                if n.text and n.text.strip():
                    stack.append((path + ("_text",), None))
                for attr in reversed(list(n.attrib)):
                    stack.append((path + ("@" + attr,), None))
                stack.append((path + ("#num",), None))

        stack = [(tuple(), subtree_by_tag)]
        while stack:
            path, subtree_by_tag = stack.pop()
            if path and path[-1]:
                tag_type = path[-1][0]
                if tag_type in ("@", "#", "_"):
                    yield path
            for t2, d2 in reversed(subtree_by_tag.items()):
                stack.append((path + (t2,), d2))

    def _find_non_terminal_and_order_bottom_up(self):
        nodes = []
        queue = [((self._root.tag,), self._root)]
        while queue:
            tags, n = queue.pop()
            nodes.insert(0, (tags, n))
            for c in n:
                if list(c) or c.attrib:
                    queue.insert(0, (tags + (c.tag,), c))

        return nodes

    def _flatten(self, bottom_up_nodes: List[Tuple[Path, Element]]):
        # inverted BFS, non terminal nodes
        for path, node in bottom_up_nodes:
            row_dicts_by_tag = self._group_children_by_path(path, node)
            new_row_dicts = self._flatten_tags(row_dicts_by_tag)
            attrs = self._create_attrs(path, node)
            self.row_dicts_by_element[node] = [{**attrs, **rd} for rd in
                                               new_row_dicts]
        self.row_dicts_by_element[self._root] = self._rows_with_preamble_added(
            (self._root.tag,), self._root, 0)

    def _group_children_by_path(self, path: Path, node: ET.Element
                                ) -> Dict[Path, List[RowDict]]:
        counter = collections.Counter()
        row_dicts_by_tag = {}

        for child in node:
            num = counter[child.tag]
            cur_path = path + (child.tag,)
            rows_with_preamble = self._rows_with_preamble_added(
                cur_path, child, num)
            self._add_new_rows_to_child_tag(row_dicts_by_tag,
                                            child.tag,
                                            rows_with_preamble)
            counter[child.tag] += 1
        return row_dicts_by_tag

    def _rows_with_preamble_added(self, path: Path, node: Element, num: int
                                  ) -> List[RowDict]:
        preamble = {path + ("#num",): num}
        if node.text and node.text.strip():
            preamble[path + ("_text",)] = node.text.strip()
        row_dicts = self.row_dicts_by_element.get(node, [{}])
        return [{**preamble, **rd} for rd in row_dicts]

    def _add_new_rows_to_child_tag(
            self, row_dicts_by_tag: Dict[str, List[RowDict]],
            tag: str,
            new_rows: List[RowDict]):
        if tag in row_dicts_by_tag:
            row_dicts_by_tag[tag].extend(new_rows)
        else:
            row_dicts_by_tag[tag] = new_rows

    def _flatten_tags(self, row_dicts_by_tag: Dict[str, List[RowDict]]
                      ) -> List[RowDict]:
        if row_dicts_by_tag:
            new_rows = self._product_elements(row_dicts_by_tag)
        else:
            new_rows = [{}]
        return new_rows

    def _create_attrs(self, path: Path, node: ET.Element) -> RowDict:
        attrs = {}
        for attr, value in node.attrib.items():
            attr_path: Path = path + (("@" + attr),)
            attrs[attr_path] = value
        return attrs

    def _product_elements(self, row_dicts_by_tag: Dict[str, List[RowDict]]
                          ) -> List[RowDict]:
        # in most cases: concatenation of rows (each tag once) or a set of rows
        # (n-times a tag)

        # first, merge by alias since we multlipy rows of a tag by rows of
        # another tag iff the latter is not an alias of the former.
        row_dicts_by_tag_or_alias = {}
        for tag, rd in row_dicts_by_tag.items():
            row_dicts_by_tag_or_alias.setdefault(self._aliases.get(tag, tag),
                                                 []).extend(rd)

        list_of_row_dicts: List[List[RowDict]] = list(
            row_dicts_by_tag_or_alias.values())
        if len(list_of_row_dicts) == 0:
            new_row_dicts = [{}]
        elif len(list_of_row_dicts) == 1:
            new_row_dicts = list_of_row_dicts[0]
        else:
            new_row_dicts = [
                {k: v for row_dict in row_dicts for k, v in row_dict.items()}
                for row_dicts in
                itertools.product(*list_of_row_dicts)]
        return new_row_dicts


def xml2csv(filename, short_names=False, aliases=None):
    tree = ET.parse(filename)
    flattener = Flattener(tree.getroot(), short_names=short_names,
                          aliases=aliases)
    writer = csv.writer(sys.stdout, delimiter='\t')

    for r in flattener.flatten():
        writer.writerow(r)


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
    parser.add_argument('-s', '--shortnames',
                        help='use short names for columns', action='store_true')
    parser.add_argument('-a', '--aliases', default=None,
                        help='set aliases as a python dictionary', action=ParseDictAction)
    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    xml2csv(args.filename, args.shortnames, args.aliases)
