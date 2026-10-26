# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

import pytest

from KicadModTree.nodes.Container import Container, MultipleParentsError
from KicadModTree.nodes.Node import Node


class HelperTestChildNode(Node):
    def __init__(self):
        Node.__init__(self)


def testInit():
    node = Container[Node]()
    assert node.parent is None
    assert node.root is node
    assert len(node.children) == 0


def testAppend():
    node = Container[Node]()
    assert len(list(node.children)) == 0

    childNode1 = Node()
    node.append(childNode1)
    assert childNode1 in node.children
    assert childNode1.parent == node
    assert len(node.children) == 1

    childNode2 = Node()
    node.append(childNode2)
    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert len(node.children) == 2

    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert len(node.children) == 2

    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert len(node.children) == 2

    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert len(node.children) == 2

    with pytest.raises(MultipleParentsError):
        node.append(childNode1)
    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert len(node.children) == 2

    childNode3 = HelperTestChildNode()
    node.append(childNode3)
    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode3 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert childNode3.parent == node
    assert len(node.children) == 3


def testExtend():
    node = Container[Node]()
    assert len(list(node.children)) == 0

    childNode1 = Node()
    childNode2 = Node()
    node.extend([childNode1, childNode2])
    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert len(node.children) == 2

    childNode3 = Node()
    node.extend([childNode3])
    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode3 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert childNode3.parent == node
    assert len(node.children) == 3

    node.extend([])
    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode3 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert childNode3.parent == node
    assert len(node.children) == 3

    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode3 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert childNode3.parent == node
    assert len(node.children) == 3

    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode3 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert childNode3.parent == node
    assert len(node.children) == 3

    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode3 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert childNode3.parent == node
    assert len(node.children) == 3

    with pytest.raises(MultipleParentsError):
        node.extend([childNode1])
    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode3 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert childNode3.parent == node
    assert len(node.children) == 3

    childNode4 = Node()
    childNode5 = Node()
    with pytest.raises(MultipleParentsError):
        node.extend([childNode4, childNode5, childNode5])
    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode3 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert childNode3.parent == node
    assert childNode4.parent == node
    assert childNode5.parent == node
    assert len(node.children) == 5


def testRemove():
    node = Container[Node]()
    assert len(list(node.children)) == 0

    childNode1 = Node()
    childNode2 = Node()
    node.extend([childNode1, childNode2])
    assert childNode1 in node.children
    assert childNode2 in node.children
    assert childNode1.parent == node
    assert childNode2.parent == node
    assert len(node.children) == 2

    node.remove(childNode1)
    assert childNode1 not in node.children
    assert childNode2 in node.children
    assert childNode1.parent is None
    assert childNode2.parent == node
    assert len(node.children) == 1

    node.remove(childNode1)
    assert childNode1 not in node.children
    assert childNode2 in node.children
    assert childNode1.parent is None
    assert childNode2.parent == node
    assert len(node.children) == 1

    assert childNode1 not in node.children
    assert childNode2 in node.children
    assert childNode1.parent is None
    assert childNode2.parent == node
    assert len(node.children) == 1

    assert childNode1 not in node.children
    assert childNode2 in node.children
    assert childNode1.parent is None
    assert childNode2.parent == node
    assert len(node.children) == 1

    assert childNode1 not in node.children
    assert childNode2 in node.children
    assert childNode1.parent is None
    assert childNode2.parent == node
    assert len(node.children) == 1


def testInsert():
    node = Container[Node]()
    assert len(list(node.children)) == 0

    childNode1 = Container[Node]()
    node.insert(childNode1)
    assert childNode1 in node.children
    assert childNode1.parent == node
    assert len(node.children) == 1

    childNode2 = Container[Node]()
    node.insert(childNode2)
    assert childNode1 in childNode2.children
    assert childNode1 not in node.children
    assert childNode2 in node.children
    assert childNode1.parent == childNode2
    assert childNode2.parent == node
    assert len(node.children) == 1
    assert len(childNode1.children) == 0
    assert len(childNode2.children) == 1


def testInsertWithManyChildren():
    node = Container[Node]()
    assert len(list(node.children)) == 0

    for i in range(0, 200):
        node.append(Node())

    insertNode = Container[Node]()
    assert len(list(node.children)) == 200
    assert len(list(insertNode.children)) == 0
    node.insert(insertNode)
    assert len(node.children) == 1
    assert len(insertNode.children) == 200


def testRemoveTraversed():
    parent = Container[Node]()
    gen1a = Container[Node]()
    gen1b = Container[Node]()
    gen1a1 = Node()
    gen1a2 = Node()

    gen1a.append(gen1a1)
    gen1a.append(gen1a2)
    parent.append(gen1a)
    parent.append(gen1b)

    assert len(parent.children) == 2
    assert len(gen1a.children) == 2
    assert len(gen1b.children) == 0

    # try to remove gen1a1 from parent directly
    parent.remove(gen1a1)
    assert len(parent.children) == 2
    assert len(gen1a.children) == 2
    assert gen1a1.parent is not None
    assert len(gen1b.children) == 0

    # remove gen1a1 from parent (traversing through the hierarchy))
    parent.remove(gen1a1, traverse=True)
    assert len(parent.children) == 2
    assert len(gen1a.children) == 1
    assert gen1a1.parent is None
    assert len(gen1b.children) == 0

    # remove gen1a from parent
    parent.remove(gen1a)
    assert len(parent.children) == 1
    assert len(gen1a.children) == 1
    assert gen1a.parent is None
    assert len(gen1b.children) == 0


def testIter():
    node = Container[Node]()
    node.extend([Node() for _ in range(3)])
    assert len(node) == 3

    count = 0
    for _ in node.children:
        count += 1
    assert count == len(node)

    count = 0
    for _ in node:
        count += 1
    assert count == len(node.children)
    assert count == len(node)
