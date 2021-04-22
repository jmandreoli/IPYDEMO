# File:                 fractals/core.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Fractal definition and visual exploration
#

import logging
logger = logging.getLogger(__name__)

from itertools import islice, count
from numpy import sqrt, zeros, seterr, abs, nan, isnan, linspace
from .util import MultizoomAnimation
from .. import Setup

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

Parameter *main* is assumed to be function :math:`u` implemented as a ufunc.

Parameter *eoracle* is an escape oracle of the fractal, i.e. a boolean function :math:`R` such that if :math:`R(z_n(c))` for some :math:`n`, then the sequence :math:`(z_n(c))_{n\in\mathbb{N}}` is provably unbounded and :math:`c` does not belong to the fractal. If *eoracle* is given as a number `r`, then it is taken to be the function `(lambda z: abs(z)>r)`.

Attributes and methods:
  """
#==================================================================================================

  @Setup(
    'main: generator of fractal views at increasing precision',
    'eoracle: escape oracle of the fractal',
    'ibounds: area of interest of the fractal',
  )
  def __init__(self,main,eoracle=None,ibounds=None):
    self.main = main
    self.eoracle = (lambda z,r=eoracle: abs(z)>r) if isinstance(eoracle,(int,float)) else eoracle
    self.ibounds = ibounds

#--------------------------------------------------------------------------------------------------
  def temperature(self,grid):
    r"""
:param grid: an array of complex numbers

Successively yields the "temperature" grid :math:`\theta_n(c)` taken on all the points :math:`c` in *grid* for :math:`n=1\ldots\infty`, where

.. math::

   \begin{equation*}
   \theta_n(c) = \frac{\min\{m<n\;|\; |z_m(c)|>R\}\cup\{n\}}{n}
   \end{equation*}

In other words, the temperature :math:`\theta_n(c)` of a point :math:`c` is the proportion of times in the sequence :math:`(z_m(c))_{m=0:n-1}` when the value was within the escape radius. A temperature of :math:`1` characterises a point whose membership of this fractal is not decided yet (it has always been seen within the escape radius until now, but could escape later). A temperature below :math:`1` characterises a point which is provably out of this fractal, and the value of the temperature reflects the effort (number of iterations) that was required to reach that decision. Note that when :math:`n\rightarrow\infty`, the temperature :math:`\theta_n(c)` tends to :math:`1` if :math:`c` belongs to this fractal, and :math:`0` otherwise.
    """
#--------------------------------------------------------------------------------------------------
    eoracle = self.eoracle
    s = grid.shape
    tmd,tmap,sel = zeros(s,int),zeros(s,float),zeros(s,bool)
    z = grid.copy()
    for n in count(1):
      s = seterr(invalid='ignore')
      sel[...] = eoracle(z)
      seterr(**s)
      z[sel] = nan
      tmd[~isnan(z)] += 1
      tmap[...] = tmd/n
      yield tmap
      z[...] = self.main(z,grid)

#--------------------------------------------------------------------------------------------------
  def display(self,ax,maxiter=None,resolution=None,ibounds=None,cmap='jet',**ka):
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
#--------------------------------------------------------------------------------------------------
    if ibounds is None: ibounds = self.ibounds
    img = ax.imshow(zeros((1,1),float),vmin=0.,vmax=1.,origin='lower',extent=ibounds[0]+ibounds[1],cmap=cmap,interpolation='bilinear')
    def frames(bounds):
      xb, yb = bounds
      r = (yb[1]-yb[0])/(xb[1]-xb[0])
      Ny = int(sqrt(resolution*r)); Nx = int(resolution/Ny)
      grid = linspace(xb[0],xb[1],Nx,dtype=complex)[None,:]+1.j*linspace(yb[0],yb[1],Ny,dtype=complex)[:,None]
      return islice(((tmap,bounds) for tmap in self.temperature(grid)),maxiter)
    def disp_(frm):
      tmap,bounds = frm
      img.set_array(tmap)
      img.set_extent(bounds[0]+bounds[1])
      img.changed()
      return img,
    return MultizoomAnimation(ax,disp_,frames=frames,init_func=(lambda: None),**ka)

#--------------------------------------------------------------------------------------------------
  @Setup(
    'maxiter: max number of iterations',
    'resolution: number of pixels to display',
    'interval: inter-frame time [msec]',
    maxiter=1000,resolution=160000,interval=100
  )
  def launch(self,fig=dict(figsize=(8,8)),**ka):
    r"""
:param animate: animation optional parameters (as a dictionary)
:param fig: figure optional parameters (as a dictionary)
:param ka: passed to :meth:`display`

Creates matplotlib axes, then runs a simulation of the system and displays it as an animation on those axes, using the :mod:`matplotlib.animation` animation functionality.
    """
#--------------------------------------------------------------------------------------------------
    from matplotlib.pyplot import figure
    if isinstance(fig,dict): fig = figure(**fig)
    return self.display(fig.add_axes((0,0,1,1),xticks=(),yticks=(),aspect='equal'),repeat=False,**ka)
