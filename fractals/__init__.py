# File:                 fractals/__init__.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Fractal definition and visual exploration
#

import logging
logger = logging.getLogger(__name__)

from itertools import islice
from numpy import array, sqrt, zeros, ones, seterr, abs, nan, linspace, newaxis, greater_equal, true_divide
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

Parameter *eradius* is an escape radius of the fractal, i.e. a scalar :math:`R` such that if :math:`|z_n(c)|>R` for some :math:`n`, then the sequence :math:`(z_n(c))_{n\in\mathbb{N}}` is provably unbounded and :math:`c` does not belong to the fractal.

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

Successively yields the "temperature" grid :math:`\theta_n(c)` taken on all the points :math:`c` in *grid* for :math:`n=1\ldots\infty`, where

.. math::

   \begin{equation*}
   \theta_n(c) = \frac{\min\{m<n\;|\; |z_m(c)|>R\}\cup\{n\}}{n}
   \end{equation*}

In other words, the temperature :math:`\theta_n(c)` of a point :math:`c` is the proportion of times in the sequence :math:`(z_m(c))_{m=0:n-1}` when the value was within the escape radius. A temperature of :math:`1` characterises a point whose membership of this fractal is not decided yet (it has always been seen within the escape radius until now, but could escape later). A temperature below :math:`1` characterises a point which is provably out of this fractal, and the value of the temperature reflects the effort (number of iterations) that was required to reach that decision. Note that when :math:`n\rightarrow\infty`, the temperature :math:`\theta_n(c)` tends to :math:`1` if :math:`c` belongs to this fractal, and :math:`0` otherwise.
    """
#--------------------------------------------------------------------------------------------------
    eradius = self.eradius
    s = grid.shape
    tmd,tmap,undecided,sel = zeros(s,int),zeros(s,float),ones(s,bool),zeros(s,bool)
    seterr(invalid='ignore')
    for n,z in enumerate(self.main(grid),1):
      greater_equal(abs(z),eradius,sel)
      z[sel] = nan
      undecided[sel] = False
      tmd[undecided] += 1
      true_divide(tmd,n,tmap)
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
    img = ax.imshow(zeros((1,1),float),vmin=0.,vmax=1.,origin='lower',extent=ibounds[0]+ibounds[1],cmap='jet',interpolation='bilinear')
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
