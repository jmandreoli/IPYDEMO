:mod:`IPYDEMO.polyhedra` --- Polyhedra exploration
==================================================

This module provides tools to display and explore polyhedra.

An example
----------

The following program shows some properties of the dodecahedron

* min-edge-colouring requires 3 colours, and there are exactly 2 solution up to colour choice and permutations.
* min-threading requires 10 threads, coloured arbitrarily in the 2 generated solutions below.

.. literalinclude:: ../demo/polyhedra.py
   :language: python
   :tab-width: 2

Typical output:

.. image:: ../demo/polyhedra_ec.png

.. image:: ../demo/polyhedra_tc.png

Available types and functions
-----------------------------

.. automodule:: IPYDEMO.polyhedra.core
   :members:
   :member-order: bysource
   :show-inheritance:

.. automodule:: IPYDEMO.polyhedra.util
   :members:
   :member-order: bysource
   :show-inheritance:
