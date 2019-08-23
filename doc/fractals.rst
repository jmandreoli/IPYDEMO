:mod:`IPYDEMO.fractals` --- Fractals exploration
================================================

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

.. image:: ../demo/fractals.gif

Available types and functions
-----------------------------

.. automodule:: IPYDEMO.fractals
   :members:
   :member-order: bysource
   :show-inheritance:

.. automodule:: IPYDEMO.fractals.util
   :members:
   :member-order: bysource
   :show-inheritance:
