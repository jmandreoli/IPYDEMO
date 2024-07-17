# File:                 odesimu/core.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              ODE simulation and visualisation
#

from __future__ import annotations
import logging; logger = logging.getLogger(__name__)
from typing import Any, Union, Callable, Iterable, Mapping, Tuple

from functools import partial
from itertools import repeat, islice
from scipy.integrate import solve_ivp
from myutil.simpy import RobustEnvironment
from numpy import ndarray,array,arange,concatenate

__all__ = 'ODEEnvironment', 'System',

#==================================================================================================
class ODEEnvironment (RobustEnvironment):
  r"""
An instance of this class represents an abstract dynamical systems (in physics, electronics, hydraulics etc.) governed by an ordinary differential equation (ODE):

.. math::

   \begin{array}{rcl}
   \frac{\mathbf{d}y}{\mathbf{d}t} & = & F(t,y)
   \end{array}

where :math:`t` is the simulation time and :math:`y` is the state. The ODE numerical solver used is taken from module :mod:`scipy.integrate` which assumes the state is a :class:`numpy.array` instance or a scalar.

The initial simulation time and state are given by *init_t* and *init_y*, respectively. The ODE is solved iteratively on successive, contiguous intervals given by *period*, the simulation period generator, which generates the spans of the intervals.

* If *period* is a :class:`float` instance, the interval spans are constant equal to *period*
* If *period* is an immutable iterable of :class:`float` instances, the interval spans are taken to be these numbers
* Otherwise, *period* must be a generator of :class:`float` instances

Various specifications of the ODE are passed through *spec* to function :func:`scipy.integrate.solve_ivp`. At least function :math:`F` must be passed as keyword argument ``fun``.

The cache specification *cache* is either :const:`None`, in which case no caching is performed, or a pair of the cache length and the cache period, independent of the simulation period generator. The cache contains the states sampled at a sequence of decreasing multiples of the cache period. The size of the sequence is chosen so that at any time in the current simulation span, the sequence clipped above at that time has length at least equal to the cache length, unless the initial time is reached before.

:param init_t: initial simulation time
:param init_y: initial simulation state
:param period: period of ODE resolution
:param cache: cache specification
:param ka: dictionary of arguments passed to the ODE solver
  """
#==================================================================================================
  Exception = type('ODEException',(RuntimeError,),{})
  init_y: ndarray
  r"""Initial state"""
  statef: Callable[[float],ndarray]
  r"""Current function of simulation time returning state"""
  state: ndarray
  r"""State at the current instant of the simulation"""
  cache_length: int
  r"""Expected length of cache"""
  cache_period: float
  r"""Cache sampling period"""
  cache_last: int
  r"""Index of the last cached state"""
  cache: ndarray
  r"""The cache itself (the time axis is the last axis)"""

  def __init__(self,period:Union[float,Iterable[float],Callable[[],float]]=None,cache:Tuple[int,float]=None,init_t:float=0.,init_y:ndarray=None,**spec):
    if callable(period): period_ = period
    elif isinstance(period,float): assert period>0; period_ = partial(repeat,period)
    else: assert all((isinstance(x,float) and x>0) for x in islice(period,10)); period_ = partial(iter,period)
    self.period = period_
    self.cache_init(cache)
    self.init_y = array(init_y)
    self.spec = spec
    super().__init__(init_t)

  def reset(self):
    r"""Resets states and cache, and defines a process"""
    super().reset()
    self.process(self.trajectory())
    self.statef = (lambda t,y=self.init_y:y)
    self.state = self.init_y
    self.cache_reset()

  def trajectory(self):
    for p in self.period():
      t_f = self.now+p
      r = solve_ivp(t_span=(self.now,t_f),y0=self.statef(self.now),dense_output=True,**self.spec)
      if not r.success: self.statef = partial(self.error_statef,message=r.message); break
      self.statef = r.sol
      self.cache_update(t_f)
      yield self.timeout(p)

  def run(self,until=None):
    super().run(until)
    self.state = self.statef(self.now)

  def error_statef(self,t,message=None): raise self.Exception(message)

  def cache_init(self,spec):
    if spec is None: self.cache_reset = self.cache_update = noop
    else: self.cache_length,self.cache_period = spec

  def cache_reset(self):
    self.cache = self.init_y[:,None]
    self.cache_last = int((self.now-self.init_t)/self.cache_period)

  def cache_update(self,t_f):
    n = int((t_f-self.init_t)/self.cache_period)
    if n>self.cache_last:
      x = self.statef(self.init_t+arange(n,self.cache_last,-1)*self.cache_period)
      self.cache = concatenate((x,self.cache[:,:self.cache_length]),axis=-1)
      self.cache_last = n

  @property
  def cached_states(self):
    r"""States of a sequence of states at previous instants in the simulation"""
    n = self.cache_last-int((self.now-self.init_t)/self.cache_period)
    return self.cache[:,n:n+self.cache_length]

#==================================================================================================
class System:
  r"""
Instances of this class gather information for a simulation as implemented by class :class:`myutil.simpy.SimpySimulation`.
  """
#==================================================================================================
  factory = ODEEnvironment
  fun = None
  r"""(required) Function :math:`F` to use in the ODE :math:`\frac{\mathbf{d}y}{\mathbf{d}t}=F(t,y)`"""
  jac = None
  r"""(optional) Jacobian of the function of the ODE"""
  def makestate(self,*a,**ka):
    r"""Returns a state computed from its arguments. This implementation raises an error and must be overridden in subclasses or at the instance level."""
    raise NotImplementedError()
  def displayer(self,env,part_spec,**ka):
    r"""Returns a default displayer function which, on invocation, displays the current state of the environment *env* on the board part specified by *part_spec*. The display can be fine-tuned by keyword arguments *ka*, which can be specified as a dictionary in the last positional argument of method :meth:`launch`."""
    raise NotImplementedError()
  launch_defaults = {}
  def launch(self,*displayers,hooks=(),init_y=None,**ka):
    r"""
Returns a tuple comprising an instance of class :class:`ODEEnvironment` and various environment displayers, as expected by :class:`myutil.simpy.SimpySimulation`.

* The ODE is specified by attributes :attr:`fun` and :attr:`jac` together with the other arguments in *ka* (the value of key ``init_y`` is first passed to method :meth:`makestate` as keyword arguments if it is a dictionary, otherwise as positional arguments).
* The displayers are given by *displayers*; if its last element is a dictionary, it is replaced by the default displayer with that dictionary as keyword arguments, otherwise the default displayer is appended
    """
    init_y = self.makestate(**init_y) if isinstance(init_y,dict) else self.makestate(*init_y)
    env = self.factory(init_y=init_y,**dict(dict(fun=self.fun,jac=self.jac,**self.launch_defaults),**ka))
    for h in hooks: env = h(env)
    displayers = list(displayers)
    if displayers and isinstance(displayers[-1],dict): displayers[-1] = partial(self.displayer,**displayers[-1])
    else: displayers.append(self.displayer)
    return env,*displayers

def noop(*a,**ka): pass
