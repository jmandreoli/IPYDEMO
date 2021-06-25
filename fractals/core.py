# File:                 fractals/core.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Fractal definition and visual exploration
#

import logging
logger = logging.getLogger(__name__)

from itertools import count
from functools import partial, cached_property
from numpy import sqrt, zeros, abs, nan, isnan, linspace
from .util import Selection

__all__ = 'Fractal',

#==================================================================================================
class Fractal:
  r"""
:param main: a function (see below)
:param eoracle: escape oracle of the sequence defining this fractal object
:type eoracle: :class:`Union[float,Callable[[float],bool]]`
:param ibounds: area of interest of this fractal object, as a bounding box
:type ibounds: pair(pair(:class:`float`))

Objects of this class represent abstract fractals, defined by a function :math:`u:\mathbb{C}\times\mathbb{C}\mapsto\mathbb{C}` as the set of complex numbers :math:`c` such that the sequence

.. math::

   \begin{equation*}
   z_0(c)=c \hspace{1cm} z_{n+1}(c)=u(z_n(c),c)
   \end{equation*}

remains bounded.

An escape oracle for the fractal is a boolean function :math:`R` such that if :math:`R(z_n(c))` for some :math:`n`, then the sequence :math:`(z_n(c))_{n\in\mathbb{N}}` is provably unbounded and :math:`c` does not belong to the fractal.

:param main: function :math:`u` implemented as a ufunc
:param eoracle: escape oracle of the fractal (if given as a number `r`, then it is taken to be the function `(lambda z: abs(z)>r)`)
:param ibounds: rectangle of interest of the fractal as (x-min,x-max),(y-min,y-max))

Attributes and methods:
  """
#==================================================================================================

  def __init__(self,main,eoracle=None):
    self.main = main
    self.eoracle = (lambda z,r=float(eoracle): abs(z)>r) if isinstance(eoracle,(int,float)) else eoracle

#--------------------------------------------------------------------------------------------------
  def generate(self,grid):
    r"""
:param grid: an array of complex numbers

Successively yields the "temperature" grid :math:`\theta_n(c)` taken on all the points :math:`c` in the grid for :math:`n=1\ldots\infty`, where

.. math::

   \begin{equation*}
   \theta_n(c) = \frac{\min\{m<n\;|\; R(z_m(c))\}\cup\{n\}}{n}
   \end{equation*}

In other words, the temperature :math:`\theta_n(c)` of a point :math:`c` is the proportion of times in the sequence :math:`(z_m(c))_{m=0:n-1}` when the value was outside the escape zone.

* A temperature of :math:`1` characterises a point whose membership of this fractal is not decided yet (it has never been seen in the escape zone until now, but could escape later).
* A temperature below :math:`1` characterises a point which is provably out of this fractal, and the value of the temperature reflects the effort (number of iterations) that was required to reach that decision.

Note that when :math:`n\rightarrow\infty`, the temperature :math:`\theta_n(c)` tends to :math:`1` if :math:`c` belongs to this fractal, and :math:`0` otherwise.
    """
#--------------------------------------------------------------------------------------------------
    eoracle = self.eoracle
    effort = zeros(grid.shape,int)
    z = grid.copy()
    for n in count(1):
      z[eoracle(z)] = nan
      effort[~isnan(z)] += 1
      yield effort/n
      z[...] = self.main(z,grid)

#==================================================================================================
class MultiZoomFractal (Fractal):
#==================================================================================================

  def __init__(self,*a,ibounds=None,grid=None,**ka):
    super().__init__(*a,**ka)
    self.stack = []
    self.precision = []
    self.grid = partial(self.lingrid,resolution=grid) if isinstance(grid,int) else grid
    self.push(ibounds)

  def trace(self,i,seq):
    precision = self.precision
    for x in seq: precision[i] += 1; yield precision[i],x

  def push(self,bounds,i=None):
    if i is None: i = len(self.stack)
    else: del self.stack[i:], self.precision[i:]
    p = self.precision[i-1] if i>0 else 0
    seq = self.generate(self.grid(bounds))
    for _ in range(p): next(seq)
    x = bounds,self.trace(i,seq)
    self.stack.append(x)
    self.precision.append(p)
    return x

  def lingrid(self,bounds,resolution=None):
    (xmin,xmax),(ymin,ymax) = bounds
    r = (ymax-ymin)/(xmax-xmin)
    Ny = int(sqrt(resolution*r)); Nx = int(resolution/Ny) # Ny/Nx~r and Nx.Ny~resolution
    return linspace(xmin,xmax,Nx,dtype=complex)[None,:]+1.j*linspace(ymin,ymax,Ny,dtype=complex)[:,None]

#==================================================================================================
class FractalBrowser:
  r"""
:param ax: matplotlib axes on which to display
:type ax: :class:`matplotlib.Axes` instance
:param maxiter: max number of iterations (precision is increased at each iteration)
:type maxiter: :class:`int`
:param resolution: number of pixels to display
:type resolution: :class:`int`
:param ibounds: bounding box for the initial zoom (defaults to the area of interest)

Displays this fractal, initially zooming on *ibounds*, and allows multizoom navigation.
  """
#==================================================================================================
  def __init__(self,content:MultiZoomFractal,play_kw={},**ka):
    from matplotlib.animation import FuncAnimation
    from matplotlib.patches import Rectangle
    def refresh(entry):
      nonlocal bounds,seq
      bounds,seq = entry
      img.set_extent((*bounds[0],*bounds[1]))
      display(seq)
      player.set_level(level,len(content.stack)-1)
      if level == len(content.stack)-1: rect.set(visible=False)
      else:
        (xmin,xmax),(ymin,ymax) = content.stack[level+1][0]
        rect.set(bounds=(xmin,ymin,xmax-xmin,ymax-ymin),visible=True)
      fig.canvas.draw_idle()
    def select(bounds_):
      nonlocal level
      level += 1
      refresh(content.push(bounds_,level))
    self.select = select
    def set_level(level_):
      nonlocal level
      level = level_
      refresh(content.stack[level])
    self.set_level = set_level
    def set_running(b=None):
      nonlocal running
      running = b = ((not running) if b is None else b)
      if b: anim.resume()
      else: anim.pause()
      player.set_running(b)
    self.set_running = set_running
    def frames():
      set_running(False)
      while True: yield seq
    def display(seq):
      p,a = next(seq)
      player.set_precision(p)
      img.set_array(a)
    running,level,(bounds,seq) = None,0,content.stack[0]
    self.player = player = self.player_factory(self,**play_kw)
    fig = player.board
    ax = fig.add_axes((0,0,1,1),xticks=(),yticks=(),aspect='equal',navigate=False)
    img = ax.imshow(zeros((1,1),float),vmin=0.,vmax=1.,extent=(*bounds[0],*bounds[1]),origin='lower',cmap='jet',interpolation='bilinear')
    rect = ax.add_patch(Rectangle((0,0),width=0,height=0,alpha=.2,color='k',visible=False,lw=3,zorder=5))
    self.selection = Selection(ax,select,alpha=.4,zorder=10)
    self.anim = anim = FuncAnimation(fig,display,frames,init_func=(lambda:None),repeat=False,**ka)

  @cached_property
  def player_factory(self):
    from matplotlib import get_backend
    from .util import widget_player,mpl_player
    return widget_player if 'ipympl' in get_backend() else mpl_player

  def _ipython_display_(self): return self.player._ipython_display_()
