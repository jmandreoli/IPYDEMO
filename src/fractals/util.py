# File:                 fractals/util.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Utilities for fractal display
#

from __future__ import annotations

import traceback
from typing import Any, Union, Callable, Iterable, Mapping, Sequence, Tuple
import logging; logger = logging.getLogger(__name__)
from functools import cached_property
from matplotlib.backend_bases import MouseButton

#==================================================================================================
class FractalBrowser:
#==================================================================================================
  player = None
  r"""The player object to run the simulation"""
  player_defaults = {'interval':40}
  r"""The default arguments passed to the player factory"""
  @cached_property
  def player_factory(self)->Callable:
    r"""
  The factory to create the :attr:`player` object. This implementation assumes the board is a :mod:`matplotlib` figure, and the control panel factory is the default one as defined in :mod:`.simpy`.
    """
    from .animation import ControlledAnimation
    return ControlledAnimation

  def __init__(self,content,displayer_kw:Mapping[str,Any]|None=None,**ka):
    display = (lambda i,new: None)
    self.player = self.player_factory((lambda i,new=None: display(i,new)),**(self.player_defaults|ka))
    ax = self.player.board.add_axes((0,0,1,1),xticks=(),yticks=(),aspect='equal',navigate=False)
    self.selection = Selection(ax,self.player.select,alpha=.4,zorder=10)
    display = content.displayer(ax,**(displayer_kw or {}))
    if (b:=getattr(self.player,'_repr_mimebundle_',None)) is not None: self._repr_mimebundle_ = b

#==================================================================================================
class Selection:
#==================================================================================================
  def __init__(self,ax,callback=None,min_size=1e-10,**ka):
    from matplotlib.patches import Rectangle
    ax.figure.canvas.mpl_connect('button_press_event',self.start)
    ax.figure.canvas.mpl_connect('button_release_event',self.stop)
    ax.figure.canvas.mpl_connect('motion_notify_event',self.updt)
    self.canvas = ax.figure.canvas
    self.rec = ax.add_patch(Rectangle((0,0),width=0,height=0,color='k',visible=False,**ka))
    self.min_size = min_size
    self.bbox = None
    self.callback = callback

  def start(self,ev):
    if ev.inaxes is self.rec.axes and ev.button == MouseButton.LEFT and self.bbox is None:
      p = ev.xdata, ev.ydata
      self.bbox = [p,p]
      self.rec.set(xy=p,width=0,height=0,visible=True)
      self.canvas.draw_idle()

  def updt(self,ev):
    if ev.inaxes is self.rec.axes and self.bbox is not None:
      p = self.bbox[0]
      p1 = self.bbox[1] = ev.xdata, ev.ydata
      self.rec.set(width=p1[0]-p[0],height=p1[1]-p[1])
      self.canvas.draw_idle()

  def stop(self,ev):
    if ev.inaxes is self.rec.axes and ev.button == MouseButton.LEFT and self.bbox is not None:
      p,p1 = self.bbox
      self.bbox = None
      self.rec.set(visible=False)
      if abs(p1[0]-p[0])<self.min_size or abs(p1[1]-p[1])<self.min_size: self.canvas.draw_idle()
      else: self.callback((tuple(sorted((p[0],p1[0]))),tuple(sorted((p[1],p1[1])))))
