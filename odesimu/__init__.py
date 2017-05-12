# File:                 odesimu/__init__.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              ODE simulation and visualisation
#

import logging
logger = logging.getLogger(__name__)

from functools import partial
from numpy import zeros, nan, infty
from scipy.integrate import ode
from ..util import Setup

"""
This module provides tools to easily implement simulations of dynamical systems defined by ODE's.
"""

#==================================================================================================
class System:
  r"""
Objects of this class represent abstract dynamical systems (in physics, electronics, hydraulics etc.) governed by an ordinary differential equation (ODE):

.. math::

   \begin{array}{rcl}
   \frac{\mathbf{d}s}{\mathbf{d}t} & = & F(t,s)
   \end{array}

where :math:`s` is the state and :math:`t` is time. The ODE numerical solver used is taken from module :mod:`scipy.integrate` which assumes the state is a :class:`numpy.array` instance or a scalar. For display purposes, each state is associated with two pieces of information:

* a "live" display information which the object must be capable of interpreting to actually display its state, and

* a "shadow" display information which the object buffers during a simulation and must be capable of interpreting to render a shadow of its last states.

Attributes and methods:
  """
#==================================================================================================

#--------------------------------------------------------------------------------------------------
  @staticmethod
  def main(t,state):
    r"""
:param t: current time
:param state: current state of the system
:type state: :class:`numpy.ndarray`
:rtype: :class:`numpy.ndarray`

This is function :math:`F` defining the ODE. Returns the temporal derivative of the state when the system is in state *state* at time *t*. Hence the returned array must have the same shape as *state*. This implementation raises an error, so this method must be overridden in a subclass or instantiated at runtime.
    """
#--------------------------------------------------------------------------------------------------
    raise NotImplementedError()

#--------------------------------------------------------------------------------------------------
  @staticmethod
  def fordisplay(state):
    r"""
:param state: current state of the system
:type state: :class:`numpy.ndarray`

Returns the pair of the live and shadow display information associated with *state*. This implementation returns the state itself for both components. This method can be overridden in a subclass or instantiated at runtime.
    """
#--------------------------------------------------------------------------------------------------
    return state,state

  jacobian = None
  r"""The derivative w.r.t. state of function :math:`F` defining the ODE as :math:`J(t,s)_{uv}=\frac{\partial F_u}{\partial s_v}(t,s)`\, or :const:`None` if the Jacobian is too costly to compute (it is only used as an optimisation by some ODE solvers). If the state space is of dimension :math:`d`\, then the Jacobian must be of dimension :math:`d\times d`\."""

  integrator = dict(name='lsoda')
  r"""A :class:`dict` instance configuring the ODE solver to use (see :class:`scipy.integrate.ode`)"""

  shadowshape = ()
  r"""The shape (tuple of :class:`int` values) of the shadow display information to be buffered at each step. This attribute can be overridden in a subclass or instantiated at runtime."""

#--------------------------------------------------------------------------------------------------
  def runstep(self,ini,srate,maxtime=infty):
    r"""
:param ini: initial state of the system
:param srate: sampling rate in sec^-1
:param maxtime: simulation time in sec (default to infinity)

Runs a simulation of the system from the initial state *ini* (time 0) until *maxtime*, sampled at rate *srate*. The successive states are returned by an iterator.
    """
#--------------------------------------------------------------------------------------------------
    from time import perf_counter
    r = ode(self.main,self.jacobian).set_integrator(**self.integrator)
    dt = 1/srate
    start = perf_counter()
    r.set_initial_value(ini,0.)
    while r.successful():
      if r.t>maxtime: return
      yield r.t, r.y, start
      start = perf_counter()
      r.integrate(r.t+dt)
    else: raise Exception('ODE solver failed!')

#--------------------------------------------------------------------------------------------------
  def display(self,ax,disp,animate=None,taild=None,srate=None,hooks=(),**ka):
    r"""
:param ax: matplotlib axes on which to display
:type ax: :class:`matplotlib.Axes` instance
:param disp: a display function (see below)
:param animate: animation function
:param taild: shadow duration in sec
:param srate: sampling rate in sec^-1
:param hooks: list of display hooks (see below)
:param ka: argument dictionary for the simulation (passed to method :meth:`runstep`)

Runs a simulation of the system and displays it in *ax* as an animation.

This method is meant to be overridden in subclasses to perform some initialisations on *ax* and provide an appropriate value for parameter *disp*, which must be a function with three arguments: *t* (time), *live* (live display information) and *tail* (array of the shadow display information for the last *taild* seconds), and which actually performs the display.

A display hook is a function which is invoked once with argument *ax*, and returns a function which is invoked at each frame with its argument set to the time. Display hooks are meant to display side items other than the system.
    """
#--------------------------------------------------------------------------------------------------
    tailn = int(taild*srate)
    tail = zeros((tailn,)+self.shadowshape,float)
    tail[...] = nan
    ax.grid()
    hooks = list(hook for hook in (hookf(ax) for hookf in hooks) if hook is not None)
    info = self.infohook(ax,srate)
    def disp_(frm):
      t,state,start = frm
      for hook in hooks: hook(t)
      live, shadow = self.fordisplay(state)
      tail[1:] = tail[:-1]
      tail[0] = shadow
      disp(t,live,tail)
      info(t,start)
    return animate(ax.figure,interval=1000./srate,frames=partial(self.runstep,srate=srate,**ka),func=disp_)

#--------------------------------------------------------------------------------------------------
  @staticmethod
  def infohook(ax,srate):
    r"""
A display hook which displays some information about the simulation:

* a simulation clock

* the ratio between the real execution duration of one simulation step and the simulation duration of that step.

When the ratio is below one, the simulation clock is adjusted to be a real clock. If above one, the simulation clock is slower than a real clock.
    """
#--------------------------------------------------------------------------------------------------
    from matplotlib.patches import Rectangle
    from time import perf_counter
    ax.text(0.01,0.99,'time:',transform=ax.transAxes,va='top',ha='left',color='black',backgroundcolor='white',size='x-small',alpha=.8)
    simclockdisp = ax.text(0.07,0.99,'',transform=ax.transAxes,va='top',ha='left',color='black',backgroundcolor='white',size='x-small',alpha=.8)
    simclock_format = '{:.1f}s'.format
    ratio_width = 0.1
    ax.add_patch(Rectangle((.15,.99),ratio_width,-.01,transform=ax.transAxes,fill=False,ec='black',alpha=.8))
    ratiodisp = ax.add_patch(Rectangle((.15,.99),0.,-.01,transform=ax.transAxes,fill=True,lw=0,fc='gray',alpha=.8))
    ratio1disp = ax.add_patch(Rectangle((.15+ratio_width,.99),0.,-.01,transform=ax.transAxes,fill=True,lw=0,fc='black',alpha=.8))
    def info(t,start):
      ratio = srate*(perf_counter()-start)
      simclockdisp.set_text(simclock_format(t))
      ratiodisp.set_width(ratio_width*min(ratio,1.))
      ratio1disp.set_width(ratio_width*max(ratio-1.,0.))
    return info

#--------------------------------------------------------------------------------------------------
  @Setup(
    'maxtime: total simulation time length [sec]',
    'srate: sampling rate [sec^-1]',
    'taild: shadow duration [sec]',
    'hooks: tuple of display hooks',
    'ini: initial state',
    maxtime=infty,srate=25.
  )
  def launch(self,fig=dict(figsize=(9,9)),**ka):
    r"""
:param animate: animation optional parameters (as a dictionary)
:param fig: figure optional parameters (as a dictionary)
:param ka: passed to :meth:`display`

Creates matplotlib axes, then runs a simulation of the system and displays it as an animation on those axes, using the :mod:`matplotlib.animation` animation functionality.
    """
#--------------------------------------------------------------------------------------------------
    from matplotlib.pyplot import figure
    from matplotlib.animation import FuncAnimation
    if isinstance(fig,dict): fig = figure(**fig)
    animate = ka.pop('animate',{})
    return self.display(fig.add_axes((0,0,1,1),aspect='equal'),animate=partial(FuncAnimation,repeat=False,**animate),**ka)
