xml2csv - Another xml to  csv converter.

Copyright (C) 2021 J. Férard <https://github.com/jferard>

License: GPLv3

# Usage

    usage: xml2csv.py [-h] [-s] [-a ALIASES] filename
    
    Convert an XML file to a CSV file.
    
    positional arguments:
      filename              a file to convert
    
    optional arguments:
      -h, --help            show this help message and exit
      -s, --shortnames      use short names for columns
      -a ALIASES, --aliases ALIASES
                            set aliases as a python dictionary



# Another XML to CSV converter
Converting a tree to a table is not a trivial task. There are a few XML to CSV 
converters around, but I found no clear alogorithm on the internet, hence I 
created my own.

This converter is built upon the following algorithm.

First, use a DFS to store every path to a text node or an attribute. Add a path
to a mock attribute `#num` of every node. These are the columns. (Actually, 
I use two successive DFS : one to reduce the tree, the other to make
the traversal.)

Second, use a BFS to order nodes from bottom to top of the tree, the root 
being the last node. Store only nodes that are non terminal, ie with children
and/or attributes.

Third, "flatten" the tree from the bottom to the top. 

For each node, group the children by tag name. 

At the bottom level, two children having the same tag name 
(or an alias) are on two different rows, two children having different tag 
names are on the same row (each tag has his own column). If there are 
multiple tag names that are present more than once, a cartesian product is 
performed (use aliases to avoid cartesian product).

The attributes are then added, to build a small table associated to the node.

At every higher level, rows are build the same way, but those small tables are put side
by side (different tag) or stacked (same tag).

When the root is reached, the table is built.

This algorithm is not fast no memory efficient (improvements are welcome), 
but it is relatively easy to understand. 


# Example
This is the example from Python [xml.etree.ElementTree official doc](
https://docs.python.org/3/library/xml.etree.elementtree.html#parsing-xml) 

    ...$ cat tests/examples/example1.xml 
    <?xml version="1.0"?>
    <!--
        example from https://docs.python.org/3/library/xml.etree.elementtree.html#parsing-xml
      -->
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
    </data>
    ...$ python3 src/xml2csv.py -s tests/examples/example1.xml
    data.#num	country.#num	country.@name	rank.#num	rank._text	year.#num	year._text	gdppc.#num	gdppc._text	neighbor.#num	neighbor.@name	neighbor.@direction
    0	0	Liechtenstein	0	1	0	2008	0	141100	0	Austria	E
    0	0	Liechtenstein	0	1	0	2008	0	141100	1	Switzerland	W
    0	1	Singapore	0	4	0	2011	0	59900	0	Malaysia	N
    0	2	Panama	0	68	0	2011	0	13600	0	Costa Rica	W
    0	2	Panama	0	68	0	2011	0	13600	1	Colombia	E
