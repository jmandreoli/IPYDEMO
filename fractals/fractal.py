import logging
logger = logging.getLogger(__name__)

from numpy import array, sqrt, zeros, ones, seterr, abs, nan, linspace, newaxis
from itertools import islice
from .util import MultizoomAnimation

#==================================================================================================
class Fractal:
  r"""
:param main: a generator function (see below)
:param eradius: escape radius of the sequence defining this fractal object
:type eradius: :class:`float`
:param ibounds: area of interest of this fractal object, as a bounding box

Objects of this class represent abstract fractals, defined by two functions :math:`u:\mathbb{C}\mapsto\mathbb{C}` and :math:`v:\mathbb{C}\times\mathbb{C}\mapsto\mathbb{C}` as the set of complex numbers :math:`c` such that the sequence

.. math::

   \begin{equation*}
   z_0(c)=u(c) \hspace{1cm} z_{n+1}(c)=v(z_n(c),c)
   \end{equation*}

remains bounded.

Parameter *main* is assumed to be a generator function, which, given a grid of complex values :math:`c`, yields the corresponding successive grids :math:`z_n(c)` for :math:`n=0\ldots\infty`. The escape radius of a sequence is such that if the sequence reaches a value beyond that radius, it will not be bounded.

Attributes and methods:
  """
#==================================================================================================

  def __init__(self,main,eradius=None,ibounds=None):
    self.main = main
    self.eradius = eradius
    self.ibounds = ibounds

#--------------------------------------------------------------------------------------------------
  def temperature(self,grid):
    r"""
:param grid: an array of complex numbers

Successively yields the "temperature" grid :math:`\theta_n(c)` broadcast on all the elements :math:`c` of *grid* for :math:`n=0\ldots\infty`, where

.. math::

   \begin{equation*}
   \theta_n(c) = \frac{\min\{m\leq n\;|\; |z_m(c)|>R \textrm{ or } m=n\}}{n}
   \end{equation*}

In other words, the temperature :math:`\theta_n(c)` of a point :math:`c` is the proportion of times in the sequence :math:`(\hat{z}_m(c))_{m=0:n}` when the value was within the escape radius. A temperature of :math:`1.` characterises a point for which it has not been decided yet whether it belongs to this fractal (it has always been seen until now within the escape radius, but could escape later). A temperatures below one characterises a point which is provably out of this fractal, and reflects the effort (number of iterations) required to reach that decision.
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
  def display(self,ax,itermax=None,resolution=None,ibounds=None,**ka):
    r"""
:param ax: matplotlib axes on which to display
:type ax: :class:`matplotlib.Axes` instance
:param itermax: max number of iterations (precision is increased at each iteration)
:type itermax: :class:`int`
:param resolution: number of points to display
:type resolution: :class:`int`
:param ibounds: bounding box for the initial zoom (defaults to the area of interest)

Displays the subset of this fractal initially zooming on *ibounds* and allows multizoom navigation.
    """
#--------------------------------------------------------------------------------------------------
    if ibounds is None: ibounds = self.ibounds
    img = ax.imshow(zeros((1,1),float),vmin=0.,vmax=1.,origin='lower',extent=ibounds[0]+ibounds[1])
    def frames(bounds):
      xb, yb = bounds
      r = (xb[1]-xb[0])/(yb[1]-yb[0])
      Nx = int(sqrt(resolution/r)); Ny = int(resolution/Nx)
      grid = array(linspace(xb[0],xb[1],Ny),dtype=complex)[newaxis,:]+1.j*array(linspace(yb[0],yb[1],Nx),dtype=complex)[:,newaxis]
      return islice(((tmap,bounds) for tmap in self.temperature(grid)),itermax)
    def disp_(frm,interrupt=False):
      tmap,bounds = frm
      if interrupt:
        img.set_array(tmap)
        img.set_extent(bounds[0]+bounds[1])
      img.changed()
      return img,
    return MultizoomAnimation(ax,disp_,frames=frames,init_func=(lambda: None),**ka)

  launchdefaults = dict(itermax=1000,resolution=160000,interval=100,repeat=False)
#--------------------------------------------------------------------------------------------------
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
    for k,v in self.launchdefaults.items(): ka.setdefault(k,v)
    return self.display(figure(**fig).add_axes((0,0,1,1),xticks=(),yticks=()),**ka)
