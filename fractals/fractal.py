import logging
logger = logging.getLogger(__name__)

from itertools import islice
from numpy import array, sqrt, zeros, ones, seterr, abs, nan, linspace, newaxis
from .util import MultizoomAnimation
from ..util import Setup

#==================================================================================================
class Fractal:
  r"""
:param main: a generator function (see below)
:param eradius: escape radius of the sequence defining this fractal object
:type eradius: :class:`float`
:param ibounds: area of interest of this fractal object, as a bounding box
:type ibounds: pair(pair(:class:`float`))

Objects of this class represent abstract fractals, defined by two functions :math:`u:\mathbb{C}\mapsto\mathbb{C}` and :math:`v:\mathbb{C}\times\mathbb{C}\mapsto\mathbb{C}` as the set of complex numbers :math:`c` such that the sequence

.. math::

   \begin{equation*}
   z_0(c)=u(c) \hspace{1cm} z_{n+1}(c)=v(z_n(c),c)
   \end{equation*}

remains bounded.

Parameter *main* is assumed to be a generator function, which, given a complex number :math:`c`, yields the corresponding successive values of :math:`z_n(c)` for :math:`n=0\ldots\infty`. It must also work as a ufunc (i.e. when passed an array, it yields successive arrays of corresponding values).

Parameter *eradius* is an escape radius of the fractal, i.e. a scalar :math:`R` such that if :math:`|z_n(c)|>R` for some :math:`n`, then the sequence :math:`(z_n(c))_{n\in\mathbb{N}}` is unbounded and :math:`c` does not belong to the fractal.

Attributes and methods:
  """
#==================================================================================================

  @Setup(
    'main: generator of fractal views at increasing precision',
    'eradius: escape radius of the fractal',
    'ibounds: area of interest of the fractal',
  )
  def __init__(self,main,eradius=None,ibounds=None):
    self.main = main
    self.eradius = eradius
    self.ibounds = ibounds

#--------------------------------------------------------------------------------------------------
  def temperature(self,grid):
    r"""
:param grid: an array of complex numbers

Successively yields the "temperature" grid :math:`\theta_n(c)` taken on all the points :math:`c` in *grid* for :math:`n=0\ldots\infty`, where

.. math::

   \begin{equation*}
   \theta_n(c) = \frac{\min\{m\leq n\;|\; |z_m(c)|>R \textrm{ or } m=n\}}{n}
   \end{equation*}

In other words, the temperature :math:`\theta_n(c)` of a point :math:`c` is the proportion of times in the sequence :math:`(z_m(c))_{m=0:n}` when the value was within the escape radius. A temperature of :math:`1` characterises a point for which it has not been decided yet whether it belongs to this fractal (it has always been seen until now within the escape radius, but could escape later). A temperatures below :math:`1` characterises a point which is provably out of this fractal, and the value of the temperature reflects the effort (number of iterations) required to reach that decision.
    """
#--------------------------------------------------------------------------------------------------
    eradius = self.eradius
    s = grid.shape
    tmd,tmap = zeros((2,)+s,float)
    undecided = ones(s,bool)
    sel = zeros(s,bool)
    n = 0
    seterr(invalid='ignore')
    for z in self.main(grid):
      sel[...] = abs(z)>=eradius
      z[sel] = nan
      undecided[sel] = False
      n += 1
      tmd[...] = -tmap
      tmd[undecided] += 1
      tmap += tmd/n
      yield tmap

#--------------------------------------------------------------------------------------------------
  def display(self,ax,maxiter=None,resolution=None,ibounds=None,**ka):
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
    img = ax.imshow(zeros((1,1),float),vmin=0.,vmax=1.,origin='lower',extent=ibounds[0]+ibounds[1])
    def frames(bounds):
      xb, yb = bounds
      r = (xb[1]-xb[0])/(yb[1]-yb[0])
      Nx = int(sqrt(resolution/r)); Ny = int(resolution/Nx)
      grid = array(linspace(xb[0],xb[1],Ny),dtype=complex)[newaxis,:]+1.j*array(linspace(yb[0],yb[1],Nx),dtype=complex)[:,newaxis]
      return islice(((tmap,bounds) for tmap in self.temperature(grid)),maxiter)
    def disp_(frm,interrupt=False):
      tmap,bounds = frm
      img.set_array(tmap)
      if interrupt: img.set_extent(bounds[0]+bounds[1])
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
    from matplotlib.animation import FuncAnimation
    if isinstance(fig,dict): fig = figure(**fig)
    return self.display(fig.add_axes((0,0,1,1),xticks=(),yticks=()),repeat=False,**ka)
