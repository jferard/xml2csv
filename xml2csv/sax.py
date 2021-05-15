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
import io
from io import StringIO
from typing import Optional, List, Union, Tuple, Mapping
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import AttributesImpl

from _util import TEXT, NUM, ATTR, DEFAULT, make_header


class SaxColumnsFinder(ContentHandler):
    """
    A content handler that stores all columns. The columns are stored
    in a DFS order (paths) and, for each path, num, attributes, text.
    """

    def __init__(self, number_cols: bool = False):
        super().__init__()
        self._number_cols = number_cols
        self._cur_path = []
        self._paths = []
        self._chars = []
        self._terminals_by_path = {}

    def startElement(self, name: str, attrs: AttributesImpl):
        self._cur_path.append(name)
        for attr in attrs.keys():
            self._add_column(ATTR + attr)
        if self._number_cols:
            self._add_column(NUM)

    def endElement(self, name: str):
        if self._chars:
            self._add_column(TEXT)
            self._chars = False

        self._cur_path.pop()

    def _add_column(self, terminal):
        path = tuple(self._cur_path)
        if path not in self._terminals_by_path:
            self._paths.append(path)
            self._terminals_by_path[path] = set()

        if terminal not in self._terminals_by_path[path]:
            self._terminals_by_path[path].add(terminal)

    def characters(self, _content: str):
        if not self._chars and _content.strip():
            self._chars = True

    def columns(self) -> List[Tuple[str]]:
        return [path + (terminal,) for path in self._paths for terminal in
                sorted(self._terminals_by_path[path])]


def find_columns(filepath: Union[str, io.StringIO],
                 number_cols: bool = False) -> List[Tuple[str]]:
    parser = make_parser()
    handler = SaxColumnsFinder(number_cols)
    parser.setContentHandler(handler)
    parser.parse(filepath)
    return handler.columns()


class NoProductHandler(ContentHandler):
    def __init__(self, writer, columns):
        super().__init__()
        self._writer = writer
        self._columns = columns
        self._chars = []
        self._context: Optional[Context] = None

    def startElement(self, name: str, attrs: AttributesImpl):
        if self._context is None:
            self._context = Context(tuple(), name, dict(attrs), 0)
        else:
            self._context = self._context.new_child(name, dict(attrs))

    def endElement(self, name: str):
        assert self._context is not None
        text = "".join(self._chars).strip()
        self._context.add_text(text)
        if self._context.is_terminal():
            self._context.parent.store_terminal_child(self._context)
        else:  # non terminal context
            all_terminals = False
            for name, contexts in self._context.terminal_children.items():
                if len(contexts) == 1:  # terminal to merge
                    all_terminals = True
                    self._context.add_associated_tag(contexts[0])

            for name, contexts in self._context.terminal_children.items():
                if len(contexts) != 1:  # terminals to write
                    all_terminals = False
                    for i, context in enumerate(contexts):
                        context._num = i
                        row = context.row()
                        self._writer.writerow(
                            [row.get(c, DEFAULT) for c in self._columns])

            if all_terminals:
                row = self._context.row()
                self._writer.writerow(
                    [row.get(c, DEFAULT) for c in self._columns])

        self._context = self._context.parent
        self._chars = []

    def characters(self, content: str):
        self._chars.append(content)


class Context:
    def __init__(self, path: Tuple[str, ...], name: str,
                 attrs: Mapping[str, str], num: int):
        self._path = path
        self._name = name
        self._attrs = attrs
        self._terminal_children_by_name = {}
        self.parent: Optional["Context"] = None
        self._terminal = True
        self._text = None
        self._associated_tags: List[Context] = []
        self._num = num
        self._count_by_name = collections.Counter()

    def new_child(self, name: str, attrs: Mapping[str, str]) -> "Context":
        self._terminal = False
        child_path = self._path + (self._name,)
        context = Context(child_path, name, attrs, self._count_by_name[name])
        self._count_by_name[name] += 1
        context.parent = self
        return context

    def store_terminal_child(self, context: "Context"):
        self._terminal_children_by_name.setdefault(context._name, []).append(
            context)

    def is_terminal(self):
        return self._terminal

    def add_text(self, text: str):
        self._text = text

    def add_associated_tag(self, context: "Context"):
        self._associated_tags.append(context)

    @property
    def terminal_children(self) -> Mapping[str, "Context"]:
        return self._terminal_children_by_name

    def row(self):
        d = {}
        c: Context = self
        while c is not None:
            path = c._path + (c._name,)
            self.aggregate_context(d, c, path)
            for t in c._associated_tags:
                path = t._path + (t._name,)
                self.aggregate_context(d, t, path)
            c = c.parent
        return d

    def aggregate_context(self, d, c: "Context", path):
        d[path + (NUM,)] = c._num
        for k, v in c._attrs.items():
            d[path + (ATTR + k,)] = v
        if c._text:
            d[path + (TEXT,)] = c._text

    def __repr__(self):
        return "Context(path={}, name={}, attrs={}, text={})".format(self._path,
                                                                     self._name,
                                                                     self._attrs,
                                                                     self._text)


class NoProductFlattener:
    def __init__(self, filename, short_names=False, number_cols=False):
        self._filename = filename
        self._short_names = short_names
        self._number_cols = number_cols

    def flatten(self, writer):
        if isinstance(self._filename, str):
            f1 = f2 = self._filename
        else:
            text = self._filename.read()
            f1 = StringIO(text)
            f2 = StringIO(text)

        parser = make_parser()
        columns = find_columns(f1, self._number_cols)
        header = make_header(columns, self._short_names)
        writer.writerow(header)

        handler = NoProductHandler(writer, columns)
        parser.setContentHandler(handler)
        parser.parse(f2)
