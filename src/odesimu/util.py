# File:                 odesimu/util.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Utilities for ODE simulation
#

from __future__ import annotations
import logging; logger = logging.getLogger(__name__)

from numpy import ndarray, array, zeros, linspace, hstack, exp, inf, digitize, amax, iterable, isclose
from numpy.random import uniform
from functools import wraps, partial
from itertools import count
from .core import ODEEnvironment

#==================================================================================================
def buffered(T:int=None,N:int=None,page:int=0):
  r"""
:param T: size of the buffer page
:param N: number of samples taken over each page
:param page: the index of the initial leftmost buffer page

A functor (decorator) which allows limited buffering of a function over the reals. The set of reals is partitioned into contiguous intervals of length *T* called pages. Page 0 starts at 0. At any time, two adjacent pages are kept in a buffer, starting with *page* on the leftmost side. For each buffer page, the values of the function over that page are pre-computed at *N* equidistant samples. This form of buffering is useful when successive invocations of the function tend to stay within the same page, and the page change rate is lower than the invocation rate. Three cases may occur on an invocation:

* If the argument is within the buffer, the result is computed by interpolation from the pre-computed values.
* If the argument is in the page which is immediately right-adjacent (resp. left-adjacent) to the buffer, the buffer is shifted one page rightward (resp. leftward) to include the argument and the old leftmost (resp. rightmost) page is dropped.
* Otherwise the buffer is entirely reset to include the argument in its rightmost (resp. leftmost) page, depending on whether the argument is on the left (resp. right) of the current buffer.
  """
#==================================================================================================
  def transform(f):
    @wraps(f)
    def F(t):
      k,dt = divmod(t,step); r = dt/step; p,n = divmod(int(k),N); dp = p-F.page
      if dp==0: pass
      elif dp==1: n += N
      elif dp==2:
        buf[:N+1] = buf[N:]
        buf[N1:,0] += T; buf[N1:,1:] = f(buf[N1:,0:1])
        F.page += 1; n += N
      elif dp==-1:
        buf[N:] = buf[:N1]
        buf[:N,0] -=T; buf[:N,1:] = f(buf[:N,0:1])
        F.page -= 1
      else:
        if dp<0: p -= 1; n += N
        buf[:,0] = linspace(p*T,(p+2)*T,2*N+1)
        buf[:,1:] = f(buf[:,0:1])
        F.page = p
      v = buf[n:n+2,1:]
      return r*v[0]+(1.-r)*v[1]
    F.page = page
    F.step = step = T/N
    buf = linspace(page*T,(page+2)*T,2*N+1)[:,None]
    F.buffer = buf = hstack((buf,f(buf)))
    N1 = N+1
    return F
  return transform

#==================================================================================================
def blurred(level:float=None,offset=0.,chunk:int=1000,_ident=lambda f: f):
  r"""
:param level: the degree of blurring, as a positive number
:param offset: centre of blurring

A functor (decorator) which applies a multiplicative noise to a function. The multiplicative coefficient follows a log-uniform distribution between -*level* and *level*. Two invocations of the blurred function, whether they have the same argument or not, are blurred independently. *offset* if subtracted to the function before blurring and re-added afterwards.
  """
#==================================================================================================
  if not level: return _ident
  def transform(f):
    noise = (x for _ in count() for x in exp(uniform(-level,level,(chunk,*offset.shape))))  # infinite stream of noise
    @wraps(f)
    def F(*a,**ka): return (f(*a,**ka)-offset)*next(noise)+offset
    return F
  offset = array(offset)
  return transform

#==================================================================================================
class DPiecewise:
  r"""
Instances of this class implement piecewise constant functions which are dynamically constructed.

:param N: size of the buffer of change points
:param right: whether change point intervals include rightmost value (hence function is left-continuous)

Initially, the function is everywhere constant. Whenever a new change point is inserted, it must be greater than all the previous change points and all the arguments at which the function has already been evaluated, otherwise, an exception is raised. When the buffer is exceeded, old change points are forgotten and any attempt to evaluate the function before or at those old change points raises an exception.
  """
#==================================================================================================
  class Exception(Exception): pass
  right:bool
  tmax:float
  r"""largest value at which the function has been evaluated"""
  changepoint:ndarray
  r"""position of the change points"""
  value:ndarray
  r"""values on right of changepoints"""

  def __init__(self,N:int,right:bool=True):
    self.changepoint = zeros((N,),dtype=float)
    self.right = right

  def reset(self,t:float,v:iterable):
    r"""
(Re)initialises this function with a single change point at time *t* with value *v*.
    """
    if t is None: t = -inf
    v = array(v)
    self.changepoint[:] = -inf
    self.value = zeros((self.changepoint.shape[0],*v.shape),dtype=v.dtype)
    self.changepoint[-1] = self.tmax = t
    self.value[-1] = v  # only -1 needs to be initialised
    return self

  def update(self,t:float,v:iterable):
    r"""
Sets a new change point at time *t* with value *v*.
    """
    if t <= self.changepoint[-1]: raise DPiecewise.Exception('out-of-order update',t)
    if t < self.tmax: raise DPiecewise.Exception('obsolete update',t,self.tmax)
    v = array(v)
    self.changepoint[:-1] = self.changepoint[1:]
    self.value[:-1] = self.value[1:]
    self.changepoint[-1] = t
    self.value[-1] = v
    return self

  def __call__(self,t):
    r"""
Returns the value of this function at *t*. Works also as a ufunc.
    """
    if iterable(t): t = array(t,dtype=float); tmax = amax(t); q = (lambda n: n)
    else: t = array((t,),dtype=float); tmax = t[0]; q = (lambda n: n[0])
    self.tmax = max(tmax,self.tmax)
    n = digitize(t,self.changepoint,right=self.right)
    if any(n==0): raise DPiecewise.Exception('buffer exceeded',t)
    return self.value[q(n-1)]

#==================================================================================================
class Controller:
#==================================================================================================
  def __call__(self,t):
    r"""
:param t: time

Returns the action at time *t*. This implementation raises an error, so this method must be overridden in a subclass or instantiated at runtime.
    """
    raise NotImplementedError()
  def reset(self,t,o):
    r"""
:param t: time
:param o: observation

Initialises this controller. This implementation raises an error, so this method must be overridden in a subclass or instantiated at runtime.
    """
    raise NotImplementedError()
  def update(self,t,o):
    r"""
:param t: time
:param o: observation

Records an observation *o* at time *t*. This implementation raises an error, so this method must be overridden in a subclass or instantiated at runtime.
    """
    raise NotImplementedError()

#==================================================================================================
class PIDController (DPiecewise,Controller):
  r"""
Objects of this class implement rudimentary PID controllers.

:param gP,gI,gD: proportional, integration, derivative gains

An instance of this class defines the control as a piecewise constant function. A new change point is created by invoking method :meth:`update` passing it a time *t* and state *s* of the system at that time. The associated control is based on the value of function *observe* at *s*, using the PID scheme. Change points must be inserted in chronological order.
  """
#==================================================================================================
  last = None
  cumul = None

  def __init__(self,gP,gI=None,gD=None,observe=None,action=None,**ka):
    super().__init__(**ka)
    assert gP is not None
    self.gain = gP,gI,gD
    if action is not None: assert callable(action); self.action = action
    if observe is not None: assert callable(observe); self.observe = observe

  @staticmethod
  def action(x): return x
  @staticmethod
  def observe(t,s): return s

  def update(self,t,s):
    o = self.observe(t,s)
    gP,gI,gD = self.gain
    tlast,olast = self.last
    dt = t-tlast
    r  = 0.
    if gP is not None: r += gP*o
    if gD is not None: r += gD*(o-olast)/dt
    if gI is not None:
      self.cumul += .5*(olast+o)*dt
      r += gI*self.cumul
    self.last = t,o
    return super().update(t,r)

  def reset(self,t,s):
    o = self.observe(t,s)
    self.last = t,o
    self.cumul = zeros(o.shape)
    r = self.gain[0]*o
    return super().reset(t,r)

  def __call__(self,t): return self.action(super().__call__(t))

#==================================================================================================
def period_hook(control:Controller,env:ODEEnvironment):
  r"""
Modifies the simulation period of the environment *env* so that it at each beginning of period, the controller *control* is reset (first period) or updated (subsequent periods).
  """
#==================================================================================================
  def period(P=env.period):
    control.reset(env.now,env.statef(env.now))
    for p in P():
      yield p
      if control.tmax>env.now: # should not be needed but ode solver sometimes look ahead
        logger.warning('re-adjusting tmax %s -> %s',control.tmax,env.now)
        control.tmax = env.now
      control.update(env.now,env.statef(env.now))
  env.period = period
  return env

#==================================================================================================
def target_displayer(pos,**ka):
  r"""
A helper function to create a displayer of a time only function *pos* returning pairs of scalar coordinates.
  """
#==================================================================================================
  return lambda env,ax: lambda a=ax.scatter((),(),**ka): a.set_offsets(pos(env.now))

#==================================================================================================
class PIDControlledMixin:
  r"""
A helper mixin class which can be added as *first* mixin in :class:`.core.System` sub-classes.
  """
#==================================================================================================
  @staticmethod
  def pos(x):
    r"""Returns the position of the target in the Euclidian space as a function of its value *x*. This implementation assumes position equals value."""
    return x
  @staticmethod
  def gap(o,state):
    r"""Returns the gap between the observation *o* of the target and the *state* of the system. This implementation assumes the observation and state space are identical, and returns the difference between the observation and the state."""
    return o-state

  display_defaults = dict(c='g',marker='^',label='target')

  def __init__(self,control_kw,target,*a,**ka):
    blur = control_kw.pop('blur',None)
    otarget = target if blur is None else blurred(level=blur)(target) if isinstance(blur,float) else blurred(**blur)(target)
    self.target_displayer = target_displayer((lambda t: self.pos(target(t))),**self.display_defaults)
    super().__init__(PIDController(observe=(lambda t,state: self.gap(otarget(t),state)),**control_kw),*a,**ka)

  def launch(self,*displayers,**ka):
    return super().launch(self.target_displayer,*displayers,hooks=(partial(period_hook,self.control),),**ka)
