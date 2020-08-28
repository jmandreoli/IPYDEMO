# File:                 odesimu/util.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Utilities for ODE simulation
#

import logging
logger = logging.getLogger(__name__)

from numpy import array, zeros, infty, linspace, hstack, exp, infty, digitize
from numpy.random import uniform
from functools import wraps
from .. import Setup

#==================================================================================================
def buffered(T:int=None,N:int=None):
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
    buf = linspace(0,2*T,2*N+1)[:,None]
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
      else: raise buffered.Exception(de)
      v = buf[n:n+2,1:]
      return r*v[0]+(1.-r)*v[1]
    return F
  return tr
buffered.Exception = type('bufferedException',(Exception,),{})

#==================================================================================================
def blurred(level:float=None,offset=0.,M:int=1000,ident=lambda f: f):
  r"""
:param level: the degree of blurring, as a positive number.

A functor (decorator) which applies a multiplicative noise to a function. The multiplicative coefficient follows a log-uniform distribution between -*level* and *level*. Two invocations of the blurred function, whether they have the same argument or not, are blurred independently. *offset* if added to the function before blurring and subtracted afterwards.
  """
#==================================================================================================
  if not level: return ident
  def noise(M):
    while True:
      for x in exp(uniform(-level,level,(M,*offset.shape))): yield x
  def tr(f):
    b = noise(M)
    @wraps(f)
    def F(*a,**ka): return (f(*a,**ka)+offset)*next(b)-offset
    return F
  offset = array(offset)
  return tr

#==================================================================================================
class DPiecewiseFunc:
  r"""
Objects of this class implement piecewise constant functions which are dynamically constructed.

:param N: size of the buffer of change points

Initially, the function is everywhere constant. Whenever a new change point is inserted, it must be greater than all the previous change points and all the arguments at which the function has already been evaluated, otherwise, an exception is raised. When the buffer is exceeded, old change points are forgotten and any attempt to evaluate the function before or at those old change points raises an exception.
  """
#==================================================================================================
  Exception = type('DPiecewiseFuncException',(Exception,),{})
  @Setup(
    'N: size of the buffer of change points',
  )
  def __init__(self,N:int):
    self.changepoint = zeros((N,))
    self.value = None
    def call(t):
      if t>self.tmax: self.tmax = t
      n, = digitize((t,),self.changepoint,right=True)
      if n==0: raise self.Exception('buffer exceeded',t)
      return self.value[n-1]
    self.call = call

  def reset(self,t:int,v):
    r"""
(Re)initialises this function with a single change point at time *t* with value *v*.
    """
    if t is None: t = -infty
    self.changepoint[:] = -infty
    self.value = zeros((self.changepoint.shape[0],*v.shape))
    self.changepoint[-1] = self.tmax = t
    self.value[-1] = v # only -1 needs to be initialised

  def update(self,t:int,v):
    r"""
Sets a new change point at time *t* with value *v*.
    """
    if t<=self.changepoint[-1]: self.Exception('out-of-order update',t)
    if t<self.tmax: raise self.Exception('obsolete update',t)
    self.changepoint[:-1] = self.changepoint[1:]
    self.value[:-1] = self.value[1:]
    self.changepoint[-1] = t
    self.value[-1] = v

  def __call__(self,t): return self.call(t)

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
class PIDController (DPiecewiseFunc,Controller):
  r"""
Objects of this class implement rudimentary PID controllers.

:param gP,gI,gD: proportional, integration, derivative gains

An instance of this class defines the control as a piecewise constant function. A new change point is created by invoking method :meth:`update` passing it a time *t* and state *s* of the system at that time. The associated control is based on the value of function *observe* at *s*, using the PID scheme. Change points must be inserted in chronological order.
  """
#==================================================================================================
  @Setup(
    DPiecewiseFunc.__init__,
    'gP: proportional control gain as error quantity per observation quantity [err]',
    'gI: integral control gain [err.sec^-1]',
    'gD: derivative control gain [err.sec]',
    'crate: control rate [sec^-1]',
    'observe: input to observation transform',
    'action: error to output transform',
  )
  def __init__(self,gP,gI=None,gD=None,observe=None,action=None,crate:float=None,**ka):
    super().__init__(**ka)
    assert gP is not None
    last = cum = trig = None
    T = 1/crate
    if action is not None: # otherwise, output = error
      assert callable(action)
      self.call = lambda t,call=self.call: action(call(t))
    if observe is not None: # otherwise, observation = input
      assert(callable(observe))
    def update(t,o,update=self.update):
      nonlocal last, cum, trig
      if t<=trig: return
      trig = max(trig+T,t)
      tlast,olast = last
      dt = t-tlast
      r  = 0.
      if gP is not None: r += gP*o
      if gD is not None: r += gD*(o-olast)/dt
      if gI is not None:
        cum += .5*(olast+o)*dt
        r += gI*cum
      update(t,r)
      last = t,o
    if observe is not None: update = lambda t,x,update=update: update(t,observe(t,x))
    self.update = update
    def reset(t,o,reset=self.reset):
      nonlocal last, cum, trig
      trig = t+T
      last = t,o
      cum = zeros(o.shape)
      r = gP*o
      reset(t,r)
    if observe is not None: reset = lambda t,x,reset=reset: reset(t,observe(t,x))
    self.reset = reset
    self.listeners = lambda: dict(start=[lambda r: reset(r.t,r.y)],step=[lambda r: update(r.t,r.y)])

#==================================================================================================
def logger_hook(ax,logger,prefix='alt+'):
  r"""
:param ax: matplotlib axes on which to display
:type ax: :class:`matplotlib.Axes` instance
:param logger: a logger object
:type logger: :class:`logging.Logger`
:param prefix: the code of a meta-key as produced by :mod:`matplotlib`

Allows the logging level of *logger* to be controlled through the keyboard: when the canvas of *ax* has focus, pressing keys i, w, e, c while holding the *prefix* key pressed, sets the logging level to INFO, WARN, ERROR, CRITICAL respectively.
  """
#==================================================================================================
  D = dict(i=logging.INFO,w=logging.WARN,e=logging.ERROR,c=logging.CRITICAL)
  D = dict((prefix+k,v) for k,v in D.items())
  def setlevel(ev):
    lvl = D.get(ev.key)
    if lvl is not None: logger.setLevel(lvl)
  ax.figure.canvas.mpl_connect('key_press_event',setlevel)

#==================================================================================================
def marker_hook(ax,f,_dflt=dict(marker='*',c='r').items(),**ka):
  r"""
:param ax: matplotlib axes on which to display
:type ax: :class:`matplotlib.Axes` instance
:param f: a function with one parameter

A display hook which displays a single marker whose position at time *t* is given by *f(t)*.
  """
#==================================================================================================
  for k,v in _dflt: ka.setdefault(k,v)
  trg_s = ax.scatter((0,),(0,),**ka)
  return dict(step=[lambda r: trg_s.set_offsets((f(r.t),))])
