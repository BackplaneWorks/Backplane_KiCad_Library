.. KiCad Library documentation master file, created by
   sphinx-quickstart on Sun Feb 19 20:08:44 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Documentation of KiCad's Library
================================

This is the library that powers the scripts for generating the footprint and 3D model library.

There are two main components to the library:
- The `kilibs`: Generic utilities and tools for KiCad library generators, CI scripts.
- The `KicadModTree` framework which is used for footprint generation.


The kilibs
==========

This is the core library. Currently there are 4 sub-packages to the core libraray:

- `declarative_defs`: Stuff to extract and evaluate expressions from strings, dictionaries, etc. Used for example for converting the `additional_drawings` defined in YAML files into actual drawings.
- `geom`: A set of geometrical classes and tools. Two sub-sub-packages are worth mentioning:

    - `shapes`: Classes that define shapes (circles, rectangles, etc) on which a standard set of operations can be applied (`translate()`, `rotate()`, `is_point_on_self()`, etc.).
    - `tools`: Implementations of geometrical functions most of which can be applied to the shapes, such as `intersect()`, `cut()`, `keepout()`, etc.

- `ipc_tools`: Classes and functions around IPC, such as IPC rules.
- `util`: Generic tools to work with dictionaries and parameters.


The KicadModTree
================

This framework is mainly based on the idea of scripted CAD systems (for example OpenSCAD). This means, everything is a node, and can be structured like a tree.
In other words, you can group parts of the footprint, and translate them in any way you want. Also cloning & co. is no Problem anymore because of this concept.

To be able to create custom `Nodes`, The system is seperated in two parts. Base nodes, which represents simple structures and also be used by KiCad itself,
and specialized nodes which alter the behavior of base nodes (for example `Rotation`), or represent a specialized usage of base nodes (for example `Rectangle`).

When you serialize your footprint, the serialize command only has to handle base nodes, because all other nodes are based upon the base nodes.
This allows us to write specialized nodes without worrying about the FileHandlers or other core systems.
You simply create your special node, and the framework knows how to handle it seamlessly.

Note that the geometrical part of the nodes should be implemented seperately in the `shapes` package of the `kilibs`.


Module Index
============


.. autosummary::
   :toctree: _autosummary
   :template:
   :recursive:

   src.kilibs
   KicadModTree


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
