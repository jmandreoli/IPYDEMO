import logging
logger = logging.getLogger(__name__)

from time import clock
from numpy import zeros, nan, infty
from scipy.integrate import ode
from functools import partial

#--------------------------------------------------------------------------------------------------
class System (object):
  r"""
Objects of this class represent abstract dynamical systems (in physics, electronics, hydraulics etc.) governed by an ordinary differential equation (ODE):

.. math::

   \begin{array}{rcl}
   \frac{\mathbf{d}s}{\mathbf{d}t} & = & F(t,s)
   \end{array}

where :math:`s` is the state and :math:`t` is time. The ODE numerical solver used is taken from module :mod:`scipy.integrate` which assumes the state is a :class:`numpy.array`\. For display purposes, each state is associated with two pieces of information:

* a "live" display information which the object must be capable of interpreting to actually display the state, and

* a "shadow" display information which the object buffers during a simulation and must be capable of interpreting to render a shadow of the last states.

Attributes defined in subclasses (or preferably at instance level for efficiency):

.. attribute:: main

   The function :math:`F` defining the ODE.

.. attribute:: jacobian

   The derivative of function :math:`F` defining the ODE as :math:`J_{uv}(t,s)=\frac{\partial F_u}{\partial s_v}`\, or :const:`None` if the Jacobian is too costly to compute (it is only used as an optimisation by the ODE solver). If the state space is of dimension :math:`d`\, then the Jacobian must be of dimension :math:`d\times d`\.

.. attribute:: fordisplay

   A function which, given a state, returns the pair of the live and shadow display information associated with that state.

Methods:
  """
#--------------------------------------------------------------------------------------------------

  jacobian = None
  integrator = dict(name='lsoda')
  shadowshape = (2,)

  def runstep(self,ini,srate,maxtime=infty):
    r"""
:param ini: initial state of the system
:param srate: sampling rate in 1/s
:param maxtime: simulation time in s (default to infinity)

Runs a simulation of the system from the initial state *ini* (time 0) until *maxtime*\, sampled at rate *srate*\. The elements are returned by an iterator.
    """
    r = ode(self.main,self.jacobian).set_integrator(**self.integrator)
    dt = 1/srate
    r.set_initial_value(ini)
    while r.successful():
      if r.t>maxtime: return
      yield r.t, r.y
      r.integrate(r.t+dt)
    else: raise Exception('ODE solver failed!')

  def display(self,ax,disp,animate=None,taild=None,srate=None,hooks=(),**ka):
    r"""
:param ax: matplotlib axes on which to display
:type ax: :class:`matplotlib.Axes` instance
:param disp: a display function (see below)
:param simul: argument dictionary for the simulation (passed to method :meth:`runstep`)
:param animate: animation function
:param taild: shadow duration in sec
:param ini: initial state of the system
:param srate: sampling rate in sec^-1
:param hooks: list of display hooks (see below)

Runs a simulation of the system and displays it in *ax* as an animation.

This method is meant to be overridden in subclasses to perform some initialisations on *ax* and provide appropriate values for parameter *disp*\, which must be a function with three arguments: *t* (time), *live* (live display information) and *tail* (array of the shadow display information for the last *taild* seconds), and which actually performs the display.

A display hook is a function which is invoked once with argument *ax*, and returns a function which is invoked at each frame with its argument set to the time. Display hooks are meant to display side items other than the system.
    """
    tailn = int(taild*srate)
    tail = zeros((tailn,)+self.shadowshape,float)
    tail[...] = nan
    ax.grid()
    hooks = list(hook for hook in (hookf(ax) for hookf in hooks) if hook is not None)
    info = self.infohook(ax,srate)
    def disp_(frm):
      t,state = frm
      for hook in hooks: hook(t)
      live, shadow = self.fordisplay(state)
      tail[1:] = tail[:-1]
      tail[0] = shadow
      disp(t,live,tail)
      info(t)
    return animate(ax.figure,interval=1000./srate,frames=partial(self.runstep,srate=srate,**ka),func=disp_)

  @staticmethod
  def infohook(ax,srate):
    from matplotlib.patches import Rectangle
    txtstyle = dict(transform=ax.transAxes,va='top',ha='left',color='black',backgroundcolor='white',size='x-small',alpha=.8)
    ax.text(0.01,0.99,'time:',**txtstyle)
    wallclockdisp = ax.text(0.07,0.99,'',**txtstyle)
    wallclock_format = '{:.1f}s'.format
    ax.add_patch(Rectangle((.15,.99),0.1,-.01,transform=ax.transAxes,fill=False,ec='black',alpha=.8))
    loaddisp = ax.add_patch(Rectangle((.15,.99),0.,-.01,transform=ax.transAxes,fill=True,lw=0,fc='gray',alpha=.8))
    load1disp = ax.add_patch(Rectangle((.25,.99),0.,-.01,transform=ax.transAxes,fill=True,lw=0,fc='red',alpha=.8))
    cpu = clock()
    def info(t):
      nonlocal cpu
      cpu2 = clock(); r = srate*(cpu2-cpu); cpu = cpu2
      wallclockdisp.set_text(wallclock_format(t))
      loaddisp.set_width(.1*min(r,1.)); load1disp.set_width(.1*max(r-1.,0.))
    return info

  def launch(self,fig=dict(figsize=(9,9)),animate=dict(),**ka):
    r"""
:param animate: animation optional parameters (as a dictionary)
:param fig: figure optional parameters (as a dictionary)
:param ka: passed to :meth:`display`

Creates matplotlib axes, then runs a simulation of the system and displays it as an animation on those axes, using the :mod:`matplotlib.animation` animation functionality.
    """
    from matplotlib.pyplot import figure, show
    from matplotlib.animation import FuncAnimation
    self.display(figure(**fig).add_subplot(1,1,1),animate=partial(FuncAnimation,**animate),**ka)
    show()

#--------------------------------------------------------------------------------------------------
def point_display(ax,f,_dflt=dict(marker='*',c='r').items(),**ka):
  r"""
:param ax: matplotlib axes on which to display
:type ax: :class:`matplotlib.Axes` instance
:param f: a function with one parameter

A display hook which displays a single point whose position at time *t* is given by *f(t)*\.
  """
#--------------------------------------------------------------------------------------------------
  for k,v in _dflt: ka.setdefault(k,v)
  trg_s = ax.scatter((0,),(0,),**ka)
  return lambda t: trg_s.set_offsets((f(t),))

