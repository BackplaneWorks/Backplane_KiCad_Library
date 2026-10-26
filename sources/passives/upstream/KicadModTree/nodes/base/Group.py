# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2024 by C. Kuhlmann, gitlab @CKuhlmann

"""Class definition for groups."""

from __future__ import annotations

from KicadModTree.nodes.Node import Node, TStamp


class Group(Node):
    """A group."""

    _name: str
    """Name of the group."""
    _member_nodes: list[Node]
    """List of nodes that are part of the group."""
    _gathered_member_tstamp_str_set: set[str]
    """The set containing the timestamps of the member nodes."""

    def __init__(
        self,
        name: str = "",
        uuid: TStamp | None = None,
        member_tstamps: list[TStamp] | list[str] = [],
        member_nodes: list[Node] = [],
    ) -> None:
        """Create a group.

        Args:
            name: Name of the group.
            uuid: UUID of the group.
            member_tstamps: List of the UUIDs of the members.
            member_nodes: List of th member nodes.
        """
        super().__init__()

        self._name = name
        self._member_nodes = member_nodes
        # self._member_tstamps:set[TStamp]|set[str]|None  = member_tstamps

        self._gathered_member_tstamp_str_set = set()

        for m in member_tstamps:
            self._gathered_member_tstamp_str_set.add(str(m))
        for mn in member_nodes:
            ts = mn.get_timestamp()
            self._gathered_member_tstamp_str_set.add(str(ts))

    def get_group_name(self) -> str:
        """Return the group name."""
        return str(self._name)

    def get_sorted_group_member_timestamps(self) -> list[str]:
        """Return sorted timestamps of the group members."""
        return sorted(self._gathered_member_tstamp_str_set)

    def get_group_member_timestamp(self) -> set[str]:
        """Return the unsorted timestamps of the group members."""
        return self._gathered_member_tstamp_str_set

    def get_group_member_nodes(self) -> list[Node] | None:
        """Return the list of group member nodes."""
        return self._member_nodes

    def append(self, node_or_tstamp: Node | TStamp | str) -> None:
        """Append a new member node or timestamp.

        Args:
            node_or_tstamp: The node or the timestamp that shall be added to the
                group.
        """
        if isinstance(node_or_tstamp, Node):
            ts = str(node_or_tstamp.get_timestamp())
            if node_or_tstamp not in self._member_nodes:
                self._member_nodes.append(node_or_tstamp)
        elif isinstance(node_or_tstamp, TStamp):
            ts = str(node_or_tstamp.get_timestamp())
        else:
            ts = str(node_or_tstamp)
        if ts not in self._gathered_member_tstamp_str_set:
            self._gathered_member_tstamp_str_set.add(ts)

    def remove_group_item(self, node_or_tstamp: Node | TStamp | str) -> None:
        """Remove an item from the group.

        Args:
            node_or_tstamp: The node or timestamp that identifies the node that shall
                be removed.
        """
        if isinstance(node_or_tstamp, Node):
            ts = str(node_or_tstamp.get_timestamp())
            while node_or_tstamp in self._member_nodes:
                self._member_nodes.remove(node_or_tstamp)
        elif isinstance(node_or_tstamp, TStamp):
            ts = str(node_or_tstamp.get_timestamp())
        else:
            ts = str(node_or_tstamp)
        if ts in self._gathered_member_tstamp_str_set:
            self._gathered_member_tstamp_str_set.remove(ts)

    def __repr__(self) -> str:
        """The string representation of the group."""
        return (
            f"Group(name={self._name}, "
            f"member timestamps={self._gathered_member_tstamp_str_set})"
        )
