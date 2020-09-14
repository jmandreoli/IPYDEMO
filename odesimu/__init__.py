# File:                 odesimu/__init__.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              ODE simulation and visualisation
#

from __future__ import annotations
from typing import Any, Union, Callable, Iterable, Mapping, Tuple
import logging; logger = logging.getLogger(__name__)

from functools import partial
from numpy import array, zeros, nan, infty
from scipy.integrate import ode
from .. import Setup

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
  def main(t:float,state:numpy.ndarray)->numpy.ndarray:
    r"""
:param t: current time
:param state: current state of the system

This is function :math:`F` defining the ODE. Returns the temporal derivative of the state when the system is in state *state* at time *t*. Hence the returned array must have the same shape as *state*. This implementation raises an error, so this method must be overridden in a subclass or instantiated at runtime.
    """
#--------------------------------------------------------------------------------------------------
    raise NotImplementedError()

#--------------------------------------------------------------------------------------------------
  @staticmethod
  def fordisplay(state:numpy.ndarray):
    r"""
:param state: current state of the system

Returns the pair of the live and shadow display information associated with *state*. This implementation returns the state itself for both components. This method can be overridden in a subclass or instantiated at runtime.
    """
#--------------------------------------------------------------------------------------------------
    return state,state

  jacobian:Callable[[float,numpy.ndarray],numpy.ndarray] = None
  r"""The derivative w.r.t. state of function :math:`F` defining the ODE as :math:`J(t,s)_{uv}=\frac{\partial F_u}{\partial s_v}(t,s)`\, or :const:`None` if the Jacobian is too costly to compute (it is only used as an optimisation by some ODE solvers). If the state space is of dimension :math:`d`\, then the Jacobian must be of dimension :math:`d\times d`\."""

  integrator = dict(name='lsoda')
  r"""A :class:`dict` instance configuring the ODE solver to use (see :class:`scipy.integrate.ode`)"""

  shadowshape = ()
  r"""The shape (tuple of :class:`int` values) of the shadow display information to be buffered at each step. This attribute can be overridden in a subclass or instantiated at runtime."""

#--------------------------------------------------------------------------------------------------
  def runstep(self,ini:numpy.ndarray,srate:float,maxtime:float=infty,listeners:Mapping[str,List[Callable[scipy.integrate.ode]]]={}):
    r"""
:param ini: initial state of the system
:param srate: sampling rate in sec^-1
:param maxtime: simulation time in sec (default to infinity)
:param listeners: a listener binding (see below)

Runs a simulation of the system from the initial state *ini* (time 0) until *maxtime*, sampled at rate *srate*. The successive states are returned by an iterator. A listener binding associates a list of callback functions to each event of the simulation: start, stop, step, error. The callbacks are invoked with the solver object as argument when the corresponding event occurs.
    """
#--------------------------------------------------------------------------------------------------
    from time import time
    r = ode(self.main,self.jacobian).set_integrator(**self.integrator)
    dt = 1/srate
    r.set_initial_value(ini,0.)
    for f in listeners.get('start',()): f(r)
    last = time()
    while r.successful():
      r.perf = (time()-last)*srate
      yield r.t, r.y
      for f in listeners.get('step',()): f(r)
      last = time()
      if r.t>maxtime:
        for f in listeners.get('stop',()): f(r)
        return
      r.integrate(r.t+dt)
    else:
      for f in listeners.get('error',()): f(r)

#--------------------------------------------------------------------------------------------------
  def display(self,ax:matplotlib.Axes,disp:Callable[[float,numpy.ndarray,numpy.ndarray],None],hooks:List[Callable[[matplotlib.Axes],Mapping[str,List[Callable[[scipy.integrate.ode],None]]]]]=(),animate={},taild:float=None,srate:float=None,**ka):
    r"""
:param ax: matplotlib axes on which to display
:param disp: a display function (see below)
:param animate: animation function
:param taild: shadow duration in sec
:param srate: sampling rate in sec^-1
:param ka: argument dictionary for the simulation (passed to method :meth:`runstep`)
:param hooks: list of display hooks (see below)

Runs a simulation of the system and displays it in *ax* as an animation.

This method is meant to be overridden in subclasses to perform some initialisations on *ax* and provide an appropriate value for parameter *disp*, which must be a function with three arguments: *t* (time), *live* (live display information) and *tail* (array of the shadow display information for the last *taild* seconds), and which actually performs the display.

A display hook is a function which is invoked once with argument *ax*, and returns a listener binding dependent on *ax*. Display hooks are meant to display side items other than the system.
    """
#--------------------------------------------------------------------------------------------------
    from matplotlib.animation import FuncAnimation
    tailn = int(taild*srate)
    tail = zeros((tailn,*self.shadowshape),float)
    tail[...] = nan
    ax.grid()
    listeners = dict(start=[],step=[],stop=[],error=[])
    for q,L in ka.pop('listeners',{}).items(): listeners[q].extend(L)
    for hookf in (self.infohook,*hooks):
      for q,L in (hookf(ax) or {}).items(): listeners[q].extend(L)
    def disp_(frm):
      t,state = frm
      live, shadow = self.fordisplay(state)
      tail[1:] = tail[:-1]
      tail[0] = shadow
      disp(t,live,tail)
    running = True
    def toggle_anim(ev):
      nonlocal running
      if ev.inaxes is not ax or ev.key!='ctrl+ ': return
      if running: anim.event_source.stop()
      else: anim.event_source.start()
      running = not running
    ax.figure.canvas.mpl_connect('key_press_event',toggle_anim)
    anim = FuncAnimation(
      ax.figure,
      repeat=False,
      interval=1000./srate,
      frames=partial(self.runstep,srate=srate,listeners=listeners,**ka),
      func=disp_,
      **animate)
    return anim

#--------------------------------------------------------------------------------------------------
  @staticmethod
  def infohook(ax:matplotlib.Axes):
    r"""
A display hook which displays some information about the simulation:

* a simulation clock (and its lag w.r.t. the real clock)

* the performance, i.e. ratio between the real execution duration of the current simulation step and the simulation duration of that step.

If the performance is above one, the simulation clock may lag behind the real clock. But even with a performance always below one, a lag may appear and accumulate.
    """
#--------------------------------------------------------------------------------------------------
    from time import time
    top = .99
    ax.text(0.01,top,'time:',transform=ax.transAxes,va='top',ha='left',color='black',backgroundcolor='white',size='x-small',alpha=.8)
    sclockdisp = ax.text(0.07,top,'',transform=ax.transAxes,va='top',ha='left',color='black',backgroundcolor='white',size='x-small',alpha=.8)
    wclockdisp = ax.text(0.14,top,'',transform=ax.transAxes,va='top',ha='left',color='black',backgroundcolor='white',size='x-small',alpha=.8)
    ax.hlines(top,.2,.3,transform=ax.transAxes,color='gray',lw=1,alpha=.8)
    perfdisp = ax.plot((.2,.2),(top,top),'gray',(.3,.3),(top,top),'black',transform=ax.transAxes,lw=5,alpha=.8)
    enddisp = ax.text(.99,top,'',transform=ax.transAxes,va='top',ha='right',color='red',backgroundcolor='white',size='x-small')

    start = None
    def info(r):
      nonlocal start
      walltime = time()
      if start is None: start = walltime
      t = walltime-start
      sclockdisp.set_text(f'{r.t:.2f}')
      wclockdisp.set_text(f'{t:.0f}' if abs(t-r.t) >.1 else '')
      perfdisp[0].set_data((.2,.2+.1*min(r.perf,1.)),(top,top))
      perfdisp[1].set_data((.3,.3+.1*max(r.perf-1.,0.)),(top,top))
    def infoend(f):
      def F(r):
        enddisp.set_text(f(r))
        ax.figure.canvas.draw_idle() # should not be needed, mpl bug?
      return F
    return dict(step=[info],stop=[infoend(lambda r:'Simulation complete')],error=[infoend(lambda r:f'Solver failed! code:{r.get_return_code()}')])

#--------------------------------------------------------------------------------------------------
  @Setup(
    'ini: initial state',
    'srate: sampling rate [sec^-1]',
    'maxtime: total simulation time length [sec]',
    'taild: shadow duration [sec]',
    'listeners: listener binding (events: start,stop,step,error)',
    'hooks: list of display hooks',
    maxtime=infty,srate=25.,
  )
  def launch(self,fig_kw_=dict(figsize=(9,9),tight_layout=True),subplot_kw_=dict(aspect='equal'),**ka):
    r"""
:param animate: animation optional parameters (as a dictionary)
:param fig: figure optional parameters (as a dictionary)
:param ka: passed to :meth:`display`

Creates matplotlib axes, then runs a simulation of the system and displays it as an animation on those axes, using the :mod:`matplotlib.animation` animation functionality.
    """
#--------------------------------------------------------------------------------------------------
    from matplotlib.pyplot import subplots
    subplot_kw = dict(**subplot_kw_); subplot_kw.update(ka.pop('subplot_kw',{}))
    fig_kw = dict(**fig_kw_); fig_kw.update(ka.pop('fig_kw',{}))
    fig,ax = subplots(subplot_kw=subplot_kw,**fig_kw)
    return self.display(ax,**ka)
