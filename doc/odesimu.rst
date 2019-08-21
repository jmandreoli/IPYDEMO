:mod:`IPYDEMO.odesimu` --- Dynamical system simulation
======================================================

This module provides basic utilities to build system simulations based on ordinary differential equations (ODE).

An example
----------

We want to simulate the motion of a simple pendulum. The pivot of the pendulum is attached to a fixed point while the bob concentrates all the mass at a constant distance :math:`l` from the pivot. The pendulum is submitted to a constant, uniform gravity field :math:`g` oriented downwards, and frictions are ignored. The physical state of this system is entirely represented by the angle :math:`\theta` of the pendulum with the downward vertical axis, and its temporal derivative :math:`\dot{\theta}`. The equation of this elementary oscillator is given by

.. math::

   \ddot{\theta} = -\frac{g}{l}\sin\theta

The following program implements the corresponding simulation.

.. literalinclude:: ../demo/odesimu.py
   :language: python
   :tab-width: 2

The behaviour of the system is captured by class **Pendulum**, which extends class **odesimu.System**. The following methods must be provided:

* **main**, which defines the ODE of the system,
* **fordisplay**, which computes the information needed for display, and
* **display**, which actually performs the display.

Attribute **shadowshape**, which is the shape of the shadow information attached to the system, must also be provided. Method **jacobian** is optional. It defines the Jacobian of the ODE, which some ODE solvers can use for optimisation purposes. It is given here, as it is straightforward to compute.

Method **display** performs the following steps:

* apply various configurations to *ax*, which is an instance of **matplotlib.axes.Axes**: here, set the limits and the title, and draw the pivot and trajectory of the bob, as, in this simple example, it can easily be computed;
* define the matplotlib artists, initially empty, capturing the dynamic components of the simulation: here *rod_a* (pendulum's rod as a straight line segment), *bob_a* (pendulum's bob as a single point) and *shadow_a* (shadow of the buffered previous positions of the bob, as a curve);
* define the display refresher function *disp* invoked each time a new system state is computed by the ODE solver: it updates the dynamic components of the simulation;
* finally, invoke method **display** from the superclass, passing *ax* and *disp* as first two arguments.

Typical output:

.. image:: ../demo/odesimu.png
   :scale: 50

Available types and functions
-----------------------------

.. automodule:: IPYDEMO.odesimu
   :members:
   :member-order: bysource
   :show-inheritance:

.. automodule:: IPYDEMO.odesimu.util
   :members:
   :member-order: bysource
   :show-inheritance:
