:mod:`fractals` --- Fractals exploration
========================================

This module provides tools to display and explore fractals.

An example
----------

We want to explore the (most famous) fractal: Mandelbrot's set. It is the set of complex numbers :math:`c` for which the following sequence remains bounded:

.. math::

   z_0 = c \hspace{2cm} z_{n+1} = z_n^2+c

This is achieved by the following program.

.. literalinclude:: ../demo/fractals.py
   :language: python
   :tab-width: 2

Typical output:

.. image:: ../demo/fractals.png
   :scale: 50

Available types and functions
-----------------------------

.. automodule:: ipyshow.fractals.fractal
   :members:
   :member-order: bysource
   :show-inheritance:

.. automodule:: ipyshow.fractals.util
   :members:
   :member-order: bysource
   :show-inheritance:

