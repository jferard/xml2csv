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
import collections
import itertools
from io import StringIO
from typing import Tuple, List, Union, Mapping, Dict
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element

from _util import TEXT, ATTR, NUM, RowDict, Path, DEFAULT, make_header


class DomColumnsFinder:
    """
    Find columns in the dom
    """

    def __init__(self, number_cols: bool = False):
        self._number_cols = number_cols
        self._paths = []
        self._terminals_by_path = {}

    def find_columns(self, root: ET.Element) -> List[Tuple[str]]:
        stack = [((root.tag,), root)]
        while stack:
            path, node = stack.pop()
            if path not in self._terminals_by_path:
                self._paths.append(path)
                self._terminals_by_path[path] = set()

            if node is not None:
                for c in reversed(list(node)):
                    stack.append((path + (c.tag,), c))

                if self._number_cols:
                    self._terminals_by_path[path].add(NUM)
                for attr in node.attrib:
                    self._terminals_by_path[path].add(ATTR + attr)
                if node.text and node.text.strip():
                    self._terminals_by_path[path].add(TEXT)

        return [path + (terminal,) for path in self._paths for terminal in
                sorted(self._terminals_by_path[path])]


def find_columns(filepath: Union[str, StringIO],
                 number_cols: bool = False) -> List[Tuple[str]]:
    tree = ET.parse(filepath)
    root = tree.getroot()
    return DomColumnsFinder(number_cols).find_columns(root)


class ProductFlattener:
    def __init__(self, root: ET.Element, short_names: bool = False,
                 no_product=False, aliases: Mapping[str, str] = None,
                 number_cols=False):
        self._root = root
        self._short_names = short_names
        if no_product is False:
            self._aliases = {} if aliases is None else aliases
        elif aliases:
            raise ValueError()
        self._number_cols = number_cols

        self.row_dicts_by_element: Dict[ET.Element, List[RowDict]] = {}
        self.attrs_by_element: Dict[ET.Element, RowDict] = {}
        self._nodes = []

    def flatten(self):
        columns = DomColumnsFinder(self._number_cols).find_columns(self._root)
        yield make_header(columns, self._short_names)

        bottom_up_nodes = self._find_non_terminal_and_order_bottom_up()
        self._flatten(bottom_up_nodes)
        for row_dict in self.row_dicts_by_element[self._root]:
            yield [row_dict.get(col, DEFAULT) for col in columns]

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
            preamble[path + ("^text",)] = node.text.strip()
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
