# File:                 odesimu/util.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Utilities for ODE simulation
#

import logging
logger = logging.getLogger(__name__)

from numpy import zeros, infty, linspace, hstack, exp, infty, newaxis, digitize, eye
from numpy.random import uniform
from functools import wraps
from ..util import Setup

#==================================================================================================
def buffered(T=None,N=None,bufferException=type('bufferException',(Exception,),{})):
  r"""
:param T: size of the interval over which buffering is performed
:param N: number of samples taken over that interval

A functor (decorator) which allows limited buffering of a function over the positive reals. The set of positive reals is partitioned into contiguous intervals of length *T* called bins. At any time, two adjacent bins are kept in a buffer, starting with the leftmost two bins. For each buffer bin, the values of the function over that bin are pre-computed at *N* equidistant samples.

* If an invocation is requested for an argument within the buffer, the result is computed by interpolation from the pre-computed values.
* If an invocation is requested for an argument outside the buffer, it must be in the bin which is immediately right-adjacent to the buffer, otherwise an :class:`Exception` is raised. The buffer is then shifted one bin rightward to include the new bin and the old leftmost bin is dropped.
  """
#==================================================================================================
  def tr(f):
    epoch = 0
    buf = linspace(0,2*T,2*N+1)[:,newaxis]
    buf = hstack((buf,f(buf)))
    step = T/N
    @wraps(f)
    def F(t):
      nonlocal epoch
      k,dt = divmod(t,step); r=dt/step; e,n = divmod(int(k),N); de = e-epoch
      if de==0: pass
      elif de==1: n += N
      elif de==2:
        buf[:N+1] = buf[N:]
        buf[N:,0] += T; buf[N:,1:] = f(buf[N:,0:1])
        epoch += 1; n += N
      else: raise bufferException(de)
      v = buf[n:n+2,1:]
      return r*v[0]+(1.-r)*v[1]
    return F
  return tr

#==================================================================================================
def blurred(level=None,M=1000,shape=(1,),ident=lambda f: f):
  r"""
:param level: the degree of blurring, as a positive number.

A functor (decorator) which applies a multiplicative noise to a function. The multiplicative coefficient follows a log-uniform distribution between -*level* and *level*. Two invocations of the blurred function, whether they have the same argument or not, are blurred independently.
  """
#==================================================================================================
  if not level: return ident
  def noise(M):
    while True:
      for x in exp(uniform(-level,level,(M,)+shape)): yield x
  def tr(f):
    @wraps(f)
    def F(t,f=f,b=noise(M)): return f(t)*next(b)
    return F
  return tr

#==================================================================================================
class DPiecewiseFuncException(Exception): pass
class DPiecewiseFunc:
  r"""
Objects of this class implement piecewise constant functions which are dynamically constructed.

:param N: size of the buffer of change points
:param v: default value

Initially, the function is the constant function with value *v*. Whenever a new change point is inserted, it must be greater than all the previous change points and all the arguments at which the function has already been evaluated, otherwise, an exception is raised. When the buffer is exceeded, old change points are forgotten and any attempt to evaluate the function before or at those old change points raises an exception.
  """
#==================================================================================================
  @Setup(
    'N: size of the buffer of change points',
  )
  def __init__(self,N,v):
    K, = v.shape
    self.changepoint = zeros((N,))
    self.value = zeros((N,)+v.shape)
    self.default = v
    def call(t):
      if t>self.tmax: self.tmax = t
      n, = digitize((t,),self.changepoint,right=True)
      if n==0: raise DPiecewiseFuncException('buffer exceeded',t)
      return self.value[n-1]
    self.call = call

  def reset(self,v=None):
    r"""
(Re)initialises this function. Must always be called once before use.
    """
    if v is None: v = self.default
    self.changepoint[:] = -infty
    self.value[...] = v[newaxis,:]
    self.tmax = -infty

  def update(self,t,v):
    r"""
Sets a new change point at time *t* with value *v* on the right of *t*.
    """
    if t<self.tmax: raise DPiecewiseFuncException('obsolete update',t)
    self.changepoint[:-1] = self.changepoint[1:]
    self.value[:-1] = self.value[1:]
    self.changepoint[-1] = t
    self.value[-1] = v

  def __call__(self,t): return self.call(t)

#==================================================================================================
class PIDController (DPiecewiseFunc):
  r"""
Objects of this class implement rudimentary PID controllers.

:param gP,gI,gD: proportional, integration, derivative gain
:type gP,gI,gD: :class:`float`
:param observe: a function of state returning an observation of that state, or a default observation if passed :const:`None`
:param target: a function of time indicating the target value to reach

An instance of this class defines the control as a piecewise constant function. A new change point is created by invoking method :meth:`update` passing it a time *t* and state *s* of the system at that time. The associated control is based on the difference between the value of function *observe* at *s* and the value of function *target* at *t*, using the PID scheme. Change points must be inserted in chronological order.
  """
#==================================================================================================
  @Setup(
    'gP,gI,gD: control gains (proportional, integral, derivative)',
    'observe: observation function',
    'target: target function',
    gP=0.,gI=0.,gD=0.
  )
  def __init__(self,gP,gI,gD,observe,target,**ka):
    v0 = observe()
    super().__init__(v=v0,**ka)
    R = eye(len(v0.shape))
    last = None
    intg = zeros(v0.shape)
    def update(t,state,update=self.update):
      nonlocal last, intg
      v = observe(state)-target(t)
      tlast,vlast = last
      dt = t-tlast
      intg += .5*(vlast+v)*dt
      r  = - gP*v - gD*(v-vlast)/dt - gI*intg
      update(t,r)
      last = t,v
    self.update = update
    def reset(state,reset=self.reset):
      nonlocal last
      v = observe(state)-target(0)
      last = 0,v
      r = -gP*v
      reset(r)
    self.reset = reset

#==================================================================================================
def logger_hook(ax,logger,prefix='alt+'):
  r"""
Allows the logging level of *logger* to be controlled through the keyboard: when the canvas of *ax* has focus, pressing keys i, w, e, c while holding the *prefix* key pressed, sets the logging level to INFO, WARN, ERROR, CRITICAL respectively.
  """
#==================================================================================================
  D = dict(i=logging.INFO,w=logging.WARN,e=logging.ERROR,c=logging.CRITICAL)
  D = dict((prefix+k,v) for k,v in D.items())
  def setlevel(ev):
    lvl = D.get(ev.key)
    if lvl is not None: logger.setLevel(lvl)
  ax.figure.canvas.mpl_connect('key_press_event',setlevel)
