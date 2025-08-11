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
from numpy import ndarray,array
from .util import Cache

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
:param cache_spec: cache specification
:param spec: dictionary of arguments passed to the ODE solver
  """
#==================================================================================================
  Exception = type('ODEException',(RuntimeError,),{})
  init_y: ndarray
  r"""Initial state"""
  statef: Callable[[float],ndarray]
  r"""Current function of simulation time returning state"""
  state: ndarray
  r"""State at the current instant of the simulation"""
  cache: Cache
  r"""Cache of the state"""

  def __init__(self,period:Union[float,Iterable[float],Callable[[],Iterable[float]]],cache_spec:Tuple[int,float]|None=None,init_t:float=0.,init_y:ndarray=None,**spec):
    if callable(period): period_ = period
    elif isinstance(period,float): assert period>0; period_ = partial(repeat,period)
    else: assert all((isinstance(x,float) and x>0) for x in islice(period,10)); period_ = partial(iter,period)
    self.period = period_
    self.cache = Cache(self,cache_spec)
    self.init_y = array(init_y)
    self.spec = spec
    super().__init__(init_t)

  def reset(self):
    r"""Resets states and cache, and defines a process"""
    super().reset()
    self.process(self.trajectory())
    self.statef = (lambda t,y=self.init_y:y)
    self.state = self.init_y
    self.cache.reset()

  def trajectory(self):
    for p in self.period():
      t_f = self.now+p
      r = solve_ivp(t_span=(self.now,t_f),y0=self.statef(self.now),dense_output=True,**self.spec)
      if not r.success: self.statef = partial(self.error_statef,message=r.message); break
      self.statef = r.sol
      self.cache.update(t_f)
      yield self.timeout(p)

  def run(self,until=None):
    super().run(until)
    self.state = self.statef(self.now)

  def error_statef(self,t,message=None): raise self.Exception(message)

  @property
  def cached_states(self):
    r"""States at a sequence of previous instants in the simulation"""
    return self.cache.states()

#==================================================================================================
class System:
  r"""
Instances of this class gather information for a simulation as implemented by class :class:`myutil.simpy.SimpySimulation`.
  """
#==================================================================================================
  factory = ODEEnvironment
  fun:Callable[[float,ndarray],ndarray]
  r"""(required) Function :math:`F` to use in the ODE :math:`\frac{\mathbf{d}y}{\mathbf{d}t}=F(t,y)`"""
  jac:Callable[[float,ndarray],ndarray]|None = None
  r"""(optional) Jacobian of the function of the ODE"""
  def makestate(self,*a,**ka):
    r"""Returns a state computed from its arguments. This implementation raises an error and must be overridden in subclasses or at the instance level."""
    raise NotImplementedError()
  def displayer(self,env:RobustEnvironment,pane:Any,**ka)->Callable[[],None]:
    r"""Returns a default displayer function which, on invocation, displays the current state of the environment *env* on the board part specified by *pane*. This implementation raises an error and must be overridden in subclasses or at the instance level."""
    raise NotImplementedError()
  launch_defaults:dict[str,Any] = {}
  def launch(self,hooks=(),init_y=None,**ka):
    r"""
Returns an instance of class :class:`ODEEnvironment`. The ODE is specified by attributes :attr:`fun` and :attr:`jac` together with the other arguments in *ka* (the value of key ``init_y`` is first passed to method :meth:`makestate` as keyword arguments if it is a dictionary, otherwise as positional arguments).
    """
    init_y = self.makestate(**init_y) if isinstance(init_y,dict) else self.makestate(*init_y)
    ka = self.launch_defaults|ka|({'jac':self.jac} if self.jac is not None else {})
    env = self.factory(fun=self.fun,init_y=init_y,**ka)
    env.displayers['main'] = partial(self.displayer,env)
    for h in hooks: env = h(env)
    return env
