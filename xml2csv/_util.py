from typing import List, Tuple, Union, Dict

Row = List[Tuple[str, Union[int, str]]]
Path = Tuple[str, ...]
RowDict = Dict[Path, Union[int, str]]
TEXT = "^text"
ATTR = "@"
NUM = "#num"

DEFAULT = ''


def make_header(columns, short_names):
    if short_names:
        header = [".".join(c[-2:]) for c in columns]
    else:
        header = [".".join(c) for c in columns]
    return header