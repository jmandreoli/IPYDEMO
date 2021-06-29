# File:                 fractals/core.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Fractal definition and visual exploration
#

from __future__ import annotations
import logging; logger = logging.getLogger(__name__)
from typing import Any, Union, Callable, Iterable, Mapping, Tuple

from itertools import count
from functools import cached_property
from collections import namedtuple
from numpy import ndarray, sqrt, zeros, abs, nan, isnan, linspace
from .util import Selection

__all__ = 'Fractal', 'MultiZoomFractal', 'FractalBrowser',

#==================================================================================================
class Fractal:
  r"""
:param main: a function (see below)
:param eoracle: escape oracle of the sequence defining this fractal object

An instance of this class represents an abstract fractal, defined by a function :math:`u:\mathbb{C}\times\mathbb{C}\mapsto\mathbb{C}` as the set of complex numbers :math:`c` such that the sequence

.. math::

   \begin{equation*}
   z_0(c)=c \hspace{1cm} z_{n+1}(c)=u(z_n(c),c)
   \end{equation*}

remains bounded.

An escape oracle for the fractal is a boolean function :math:`R` such that if :math:`R(z_n(c))` is true for some :math:`n`, then the whole sequence :math:`(z_n(c))_{n\in\mathbb{N}}` is unbounded and :math:`c` does not belong to the fractal.

:param main: function :math:`u` implemented as a ufunc
:param eoracle: escape oracle of the fractal (if given as a number `r`, then it is taken to be the function `(lambda z: abs(z)>r)`)

Attributes and methods:
  """
#==================================================================================================

  def __init__(self,main:Callable[[complex],complex],eoracle:Union[float,Callable[[float],bool]]=None):
    self.main = main
    self.eoracle = (lambda z,r=float(eoracle): abs(z)>r) if isinstance(eoracle,(int,float)) else eoracle

#--------------------------------------------------------------------------------------------------
  def generate(self,grid):
    r"""
Successively yields the "temperature" grid :math:`\theta_n(c)` taken on all the points :math:`c` in the grid for :math:`n=1\ldots\infty`, where

.. math::

   \begin{equation*}
   \theta_n(c) = \frac{\min\{m<n\;|\; R(z_m(c))\}\cup\{n\}}{n}
   \end{equation*}

In other words, the temperature :math:`\theta_n(c)` of a point :math:`c` is the proportion of times in the sequence :math:`(z_m(c))_{m=0:n-1}` when the value was outside the escape zone.

* A temperature of :math:`1` characterises a point whose membership of this fractal is not decided yet (it has never been seen in the escape zone until now, but could escape later).
* A temperature below :math:`1` characterises a point which is provably out of this fractal, and the value of the temperature reflects the effort (number of iterations) that was required to reach that decision.

Note that when :math:`n\rightarrow\infty`, the temperature :math:`\theta_n(c)` tends to :math:`1` if :math:`c` belongs to this fractal, and :math:`0` otherwise.

:param grid: an array of complex numbers
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
  r"""
An instance of this class is a fractal together with a stack of rectangles of the complex plane, where each rectangle in the stack entirely contains its successor. For each rectangle in the stack, a grid with a certain resolution is created and the iterable of corresponding temperature grids is computed.

:param ibounds: a recommended rectangle of interest, in the form as a pair of pairs (x-min,x-max),(y-min,y-max)
  """
#==================================================================================================

  Entry = namedtuple('StackEntry','status seq bounds resolution')

  def __init__(self,*a,ibounds:Tuple[Tuple[float,float],Tuple[float,float]]=None,**ka):
    super().__init__(*a,**ka)
    self.stack = []
    self.ibounds = ibounds

  def trace(self,i,seq):
    status = self.stack[i].status
    for x in seq: status[0] += 1; status[1] = x; yield x

  def push(self,resolution,bounds=None,i=0):
    r"""
Adds the rectangle defined by *bounds* (by default the initial recommended rectangle) with resolution *resolution* at level *i* in the stack (default at the bottom of the stack). All the entries after *i* are deleted.
    """
    if bounds is None: bounds= self.ibounds
    del self.stack[i:]
    p = self.stack[i-1].status[0] if i>0 else 1
    seq = self.generate(self.grid(bounds,resolution))
    for _ in range(p): x = next(seq)
    e = self.Entry([p,x],self.trace(i,seq),bounds,resolution)
    self.stack.append(e)
    return e

  @staticmethod
  def grid(bounds:Tuple[Tuple[float,float],Tuple[float,float]]=None,resolution:int=None):
    r"""May be refined in subclasses or at the instance level"""
    (xmin,xmax),(ymin,ymax) = bounds
    r = (ymax-ymin)/(xmax-xmin)
    Ny = int(sqrt(resolution*r)); Nx = int(resolution/Ny) # Ny/Nx~r and Nx.Ny~resolution
    return linspace(xmin,xmax,Nx,dtype=complex)[None,:]+1.j*linspace(ymin,ymax,Ny,dtype=complex)[:,None]

#==================================================================================================
class FractalBrowser:
  r"""
:param content: the fractal to browse

An instance of this class is a fractal browser, which allows zooming at controlled resolution.

.. attribute player::
   An object managing the user control (selected automatically based on the :mod:`matplotlib` backend, but can be changed)
  """
#==================================================================================================

  def __init__(self,content:MultiZoomFractal,**ka):
    def displayer(fig,select):
      from matplotlib.patches import Rectangle
      ax = fig.add_axes((0,0,1,1),xticks=(),yticks=(),aspect='equal',navigate=False)
      bounds,stack,push = content.ibounds,content.stack,content.push
      img = ax.imshow(zeros((1,1),float),vmin=0.,vmax=1.,extent=(*bounds[0],*bounds[1]),origin='lower',cmap='jet',interpolation='bilinear')
      rect = ax.add_patch(Rectangle((0,0),width=0,height=0,alpha=.2,color='k',visible=False,lw=3,zorder=5))
      self.selection = Selection(ax,select,alpha=.4,zorder=10)
      level = entry = None
      def disp(i,new=None):
        nonlocal level,entry
        if i==level: a = next(entry.seq)
        else:
          level,entry = i,(stack[i] if new is None else push(*new,i))
          img.set_extent((*entry.bounds[0],*entry.bounds[1]))
          if i == len(stack)-1: rect.set(visible=False)
          else:
            (xmin,xmax),(ymin,ymax) = stack[i+1].bounds
            rect.set(bounds=(xmin,ymin,xmax-xmin,ymax-ymin),visible=True)
          a = entry.status[1]
        img.set_array(a)
        return entry.status[0]
      return disp
    self.player = self.player_factory(displayer,**ka)

  @cached_property
  def player_factory(self):
    from matplotlib import get_backend
    from .util import widget_player,mpl_player
    return widget_player if 'ipympl' in get_backend() else mpl_player

  def _ipython_display_(self): return self.player._ipython_display_()
