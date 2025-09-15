# File:                 odesimu/core.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              ODE simulation and visualisation
#

from __future__ import annotations
import logging;logger = logging.getLogger(__name__)
from typing import Any, Union, Callable, Iterable, Mapping, Tuple

from functools import partial
from itertools import repeat, islice
from inspect import signature
from scipy.integrate import solve_ivp
from numpy import ndarray,array,arange,concatenate
from myutil import ResettableSimpyEnvironment
from myutil.animation import PanesDisplayer

__all__ = 'ODESystem',

#==================================================================================================
class ODESystem:
  r"""
An instance of this class represents an abstract dynamical system (in physics, electronics, hydraulics etc.) governed by an ordinary differential equation (ODE):

.. math::

   \begin{array}{rcl}
   \frac{\mathbf{d}y}{\mathbf{d}t} & = & F(t,y)
   \end{array}

where :math:`t` is the simulation time and :math:`y` is the state. The ODE numerical solver used is taken from module :mod:`scipy.integrate` which assumes the state is a :class:`numpy.array` instance or a scalar.

This constructor does not take parameters. They are usually passed in sub-class constructors. It is still useful to call this constructor at the end as it performs a few checks.
  """
#==================================================================================================
  fun:Callable[[float,ndarray],ndarray]
  r"""(required) Function :math:`F` to use in the ODE :math:`\frac{\mathbf{d}y}{\mathbf{d}t}=F(t,y)`"""
  jac:Callable[[float,ndarray],ndarray]|None = None
  r"""(optional) Jacobian of the function of the ODE"""

  def __init__(self):
    def check(f:Callable[[float,ndarray],ndarray]):
      s = signature(f)
      assert len(s.parameters) >= 2
      if s.return_annotation not in (s.empty,ndarray): logger.warning('Function %s: %s',f,'return annotation should not be specified or should be ndarray')
      for p,names in zip(s.parameters.values(),(('t','time'),('y','state'))):
        d = ''
        if p.name not in names: d += f' name should be chosen from {names};'
        if p.default is not p.empty: d += ' default value should not be specified;'
        if p.annotation not in (p.empty,ndarray): d += ' annotation should not be specified or should be ndarray;'
        if d: logger.warning('Function %s, parameter %s:%s',f,p.name,d)
    check(self.fun)
    if self.jac is not None: check(self.jac)
    assert self.trajectory_defaults.get('fun') is None
    assert isinstance(self.trajectory_defaults.get('jac',True),bool)
    assert len(signature(self.displayer).parameters) >= 2
  trajectory_defaults:dict[str,Any] = {}
#--------------------------------------------------------------------------------------------------
  def trajectory(self,period:float|Iterable[float]|Callable[[],Iterable[float]]|None=None,init_y=None,init_t:float|None=None,cache_spec:tuple[int,float]|None=None,fun:None=None,jac:bool|None=None,**spec):
    r"""
Produces one trajectory of the ODE, as an :class:`Trajectory` instance. The trajectory is specified by its initial conditions (time *init_t* and state *init_y*), as well as a *period* specification which cuts it into contiguous time segments. At any time, the solution is available on a single segment. It is an error to compute the state at an instant which does not belong to the current segment. The *period* can be specified as

* a single (positive) :class:`float`: the segments are contiguous, of length equal to *period*
* a sequence of positive :class:`float`: the segments are contiguous, of length taken from *period*
* a positive :class:`float` generator: the segments are contiguous, of length obtained by iterating from *period*

:param period: specification of the period of the trajectory
:param init_y: initial state passed to :meth:`makestate`
:param init_t: initial time passed to :class:`float`
:param cache_spec: cache specification
:param spec: extra arguments for the ODE solver
    """
#--------------------------------------------------------------------------------------------------
    defaults = dict(self.trajectory_defaults)
    #fun
    assert fun is None
    spec['fun'] = self.fun
    # jac
    d_jac = defaults.pop('jac',False)
    if jac is None: jac = d_jac
    assert isinstance(jac,bool)
    if jac is True and (jac:=getattr(self,'jac')) is not None: spec['jac'] = jac
    # init_y
    d_init_y = defaults.pop('init_y',None)
    if init_y is None: init_y = d_init_y
    init_y = self.makestate(**init_y) if isinstance(init_y,dict) else self.makestate(*init_y)
    # init_t
    d_init_t = defaults.pop('init_t',0.)
    if init_t is None: init_t = d_init_t
    init_t = float(init_t)
    # period
    d_period = defaults.pop('period',None)
    if period is None: period = d_period
    if callable(period): period_ = period
    elif isinstance(period,float): assert period>0; period_ = partial(repeat,period)
    else: assert all((isinstance(x,float) and x>0) for x in islice(period,10)); period_ = partial(iter,period)
    # cache_spec
    d_cache_spec = defaults.pop('cache_spec',None)
    if cache_spec is None: cache_spec = d_cache_spec
    assert cache_spec is None or isinstance(cache_spec,tuple) and len(cache_spec)==2 and isinstance(cache_spec[0],int) and isinstance(cache_spec[1],float)
    spec.update(defaults)
    return Trajectory(period_,init_t,init_y,spec,cache_spec)

  def makestate(self,*a,**ka)->ndarray:
    r"""Returns a state computed from its arguments. This implementation raises an error and must be overridden in subclasses or at the instance level."""
    raise NotImplementedError()
  def displayer(self,trajectory:Trajectory,pane:Any,**ka)->Callable[[float],None]:
    r"""Returns a default displayer function which, on invocation, displays the current state of the *trajectory* on the board part specified by *pane*. This implementation raises an error and must be overridden in subclasses or at the instance level."""
    raise NotImplementedError()
#--------------------------------------------------------------------------------------------------
  def simulation(self,target=None,**ka):
    r"""
Extends a :class:`myutil.simpy.SimpySimulation` from an existing one given by *target* or a new one if *target* is :const:`None`. It adds the unrolling of the ODE resolution to the configuration of the environment, as well as the setup for the display of the solution.
    """
#--------------------------------------------------------------------------------------------------
    trajectory = self.trajectory(**ka)
    if target is None:
      target = PanesDisplayer()
      target.env = env = ResettableSimpyEnvironment(trajectory.init_t)
      target.setup = lambda t: env.run(t)
    else: assert isinstance(target,PanesDisplayer); env = target.env
    env.add_config(lambda e: e.process(e.timeout(trajectory.duration) for _ in trajectory))
    return target.add_displayer(main=partial(self.displayer,trajectory))

#==================================================================================================
class Trajectory:
  r"""
An instance of this class is an :class:`Iterable` which yields solutions to an ODE on successive, contiguous intervals. The spans of the intervals are given by a generator *period*. The initial time and state are given by *init_t* and *init_y*, respectively. The ODE itself is characterised by *spec*, passed to :func:`scipy.integrate.solve_ivp`.

A cache of solution values is also maintained at instants on a regular grid on the timeline. It is specified by *cache_spec* which is a pair, whose second component (a :class:`float`) denotes the grid step. The first component (an :class:`int`) corresponds to the desired number of cached values to be retrieved before any instant in an interval.

:param init_t: initial time
:param init_y: initial state
:param period: period of ODE resolution
:param cache_spec: cache specification as a (length,step) pair
:param spec: dictionary of arguments passed to the ODE solver
  """
#==================================================================================================
  Exception = type('TrajectoryException',(RuntimeError,),{})
  period:Callable[[],Iterable[float]]
  init_t:float
  init_y:ndarray
  spec:dict[str,Any]
  cache_spec:tuple[int,float]|None
  start:float
  r"""Start of the current trajectory interval"""
  stop:float
  r"""Stop of the current trajectory interval"""
  duration:float
  r"""Duration of the current trajectory interval"""
  state:Callable[[float|ndarray],ndarray]
  r"""Function mapping each instant between :attr:`start` and :attr:`stop` to the estimated state at that instant"""
  cached:Callable[[float],ndarray]
  r"""Function mapping each instant between :attr:`start` and :attr:`stop` to the closest cache excerpt at that instant"""
#--------------------------------------------------------------------------------------------------
  def __init__(self,period:Callable[[],Iterable[float]],init_t:float,init_y:ndarray,spec:dict[str,Any],cache_spec:tuple[int,float]|None):
#--------------------------------------------------------------------------------------------------
    self.period,self.init_t,self.init_y,self.spec,self.cache_spec = period,init_t,init_y,spec,cache_spec # immutable
    self.start,self.stop,self.duration,self.state = self.initial = init_t,init_t,0.,(lambda t,a=init_y:a)
    self.cached = init_cached = lambda t,a=init_y[:,None]: a
    if cache_spec is None:
      self.setup_cache = lambda: (init_cached,(lambda f,t: None))
    else:
      length,step = cache_spec
      def setup_cache()->tuple[Callable[[float],ndarray],Callable[[Callable[[ndarray],ndarray],float],None]]:
        last = 0; cache = init_cached(0.)
        def cached(t:float):
          n = last-int((t-init_t)/step)
          return cache[:,n:n+length]
        def update_cache(f:Callable[[ndarray],ndarray],t:float)->None:
          nonlocal cache,last
          n = int((t-init_t)/step)
          if n>last:
            x = f(init_t+arange(n,last,-1)*step)
            cache = concatenate((x,cache[:,:length]),axis=-1)
            last = n
        return cached,update_cache
      self.setup_cache = setup_cache
#--------------------------------------------------------------------------------------------------
  def __iter__(self):
#--------------------------------------------------------------------------------------------------
    self.start,self.stop,self.duration,self.state = self.initial
    self.cached,update_cache = self.setup_cache()
    spec = self.spec
    for p in self.period():
      start,stop = self.stop,self.stop+p
      r = solve_ivp(t_span=(start,stop),y0=self.state(start),dense_output=True,**spec)
      state = r.sol if r.success else partial(self.error_state,message=r.message)
      update_cache(state,stop)
      self.start,self.stop,self.duration,self.state = start,stop,p,state
      yield self
  def error_state(self,t,message=None): raise self.Exception(message)
