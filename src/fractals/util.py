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

from matplotlib import rcParams
from matplotlib.pyplot import figure
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from matplotlib.backend_bases import MouseButton
from matplotlib.patches import Rectangle
try: from myutil.ipywidgets import app, SimpleButton # so this works even if ipywidgets is not available
except: app = object

#==================================================================================================
class Selection:
#==================================================================================================
  def __init__(self,ax,callback=None,min_size=1e-10,**ka):
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

#==================================================================================================
class player_base:
  r"""
An instance of this class controls the exploration of a fractal.

:param display: a function which, given a zoom level and possibly its new specification, displays it on the board
  """
#==================================================================================================

  def __init__(self,display:Callable[[int,Any],None],**ka):
    def frames():
      self.select(None); self.setrunning(False); yield None
      while True: yield self.level
    self.level = -1
    self.anim = FuncAnimation(self.board,(lambda i: None if i is None else self.show_precision(display(i))),frames,init_func=(lambda: None),repeat=False,**ka)

  def setrunning(self,b:bool=None):
    r"""Sets the running state of the animation to *b* (if :const:`None`, the inverse of current running state)."""
    if b is None: b = not self.running
    self.running = b
    if b: self.anim.resume()
    else: self.anim.pause()
    self.show_running(b)

  def show_running(self,b:bool):
    r"""Shows the current running state as *b*. This implementation raises an error."""
    raise NotImplementedError()

  def show_precision(self,p:int):
    r"""Shows the current precision as *p*. This implementation raises an error."""
    raise NotImplementedError()

  def select(self,bounds:Union[Tuple[Tuple[float,float],Tuple[float,float]],None]):
    r"""Pushes a new level in the animation at the current level plus one. This implementation raises an error."""
    raise NotImplementedError()

#==================================================================================================
class widget_player (app,player_base):
  r"""
This class refines :class:`player_base` for backends which support :mod:`ipywidgets`.

:param displayer: passed the board figure as well as the selector on that board, returns the *display* argument of the superclass
:param resolution: the (constant) resolution for all the zoom level (total number of pixels to display)
  """
#==================================================================================================
  def __init__(self,displayer:Callable[[Figure,Selection],Callable[[int,Any],None]],resolution:int=None,fig_kw={},children=(),toolbar=(),**ka):
    from ipywidgets import BoundedIntText,IntText,Label
    def select(bounds_):
      i = self.level+1
      w_level.active = False
      w_level.max = i; w_level.value = i
      setlevel(i,(resolution,bounds_))
      w_level.active = True
    def show_running(b): w_running.icon = 'pause' if b else 'play'
    def show_precision(p): w_precision.value = p
    self.select = select
    self.show_precision = show_precision
    self.show_running = show_running
    def setlevel(i,new=None):
      self.level = i
      w_precision.value = display(i,new)
      board.canvas.draw_idle()
    # global design and widget definitions
    w_running = SimpleButton(icon='')
    w_level = BoundedIntText(0,min=0,max=0,layout=dict(width='1.6cm',padding='0cm'))
    w_level.active = True
    w_precision = IntText(0,disabled=True,layout=dict(width='1.6cm',padding='0cm'))
    super().__init__(children,toolbar=(w_running,Label('level:'),w_level,Label('precision:'),w_precision,*toolbar))
    self.board = board = self.mpl_figure(**fig_kw)
    display = displayer(board,select)
    # callbacks
    w_running.on_click(lambda b: self.setrunning())
    w_level.observe((lambda c: (setlevel(c.new) if w_level.active else None)),'value')
    super(app,self).__init__(display,**ka)

#==================================================================================================
class mpl_player (player_base):
  r"""
This class refines :class:`player_base` for backends which do not support :mod:`ipywidgets`.

:param displayer: passed the board figure as well as the selector on that board, returns the *display* argument of the superclass
:param resolution: the (constant) resolution for all the zoom level (total number of pixels to display)
  """
#==================================================================================================
  def __init__(self,displayer:Callable[[Figure,Selection],Callable[[int,Any],None]],resolution:int=None,fig_kw={},tbsize=((.15,.8,.15,1.4),.15),**ka):
    level_max = 0
    def select(bounds_):
      nonlocal level_max
      level_max = i = self.level+1
      setlevel(i,(resolution,bounds_))
    def show_running(b): play_toggler.set(text='II' if b else '|>'); toolbar.canvas.draw_idle()
    def show_precision(p): prec_disp.set(text=str(p)); toolbar.canvas.draw_idle()
    self.select = select
    self.show_running = show_running
    self.show_precision = show_precision
    def setlevel(i,new=None):
      self.level = i
      level_disp.set(text=f'{i}/{level_max}')
      show_precision(display(i,new))
      main.canvas.draw_idle()
    # global design
    tbsize_ = sum(tbsize[0])
    figsize = fig_kw.pop('figsize',None)
    if figsize is None: figsize = rcParams['figure.figsize']
    figsize_ = list(figsize); figsize_[1] += tbsize[1]; figsize_[0] = max(figsize_[0],tbsize_)
    self.main = main = figure(figsize=figsize_,**fig_kw)
    r = tbsize[1],figsize[1]
    toolbar,board = main.subfigures(nrows=2,height_ratios=r)
    self.board = board
    display = displayer(board,select)
    r = list(tbsize[0])
    r[-1] += figsize_[0]-tbsize_
    g = dict(width_ratios=r,wspace=0.,bottom=0.,top=1.,left=0.,right=1.)
    axes = toolbar.subplots(ncols=4,subplot_kw=dict(xticks=(),yticks=(),navigate=False),gridspec_kw=g)
    # widget definition
    ax = axes[0]
    play_toggler = ax.text(.5,.5,'',ha='center',va='center',transform=ax.transAxes)
    ax = axes[1]
    ax.text(.1,.5,'level:',ha='left',va='center',transform=ax.transAxes)
    level_disp = ax.text(.6,.5,'0/0',ha='left',va='center',transform=ax.transAxes)
    ax = axes[2]
    ax.set(xlim=(0,1),ylim=(0,1))
    level_ctrl, = ax.plot((0.,1.,.5,0.,.5,1.),(.5,.5,0.,.5,1.,.5),c='k')
    ax = axes[3]
    ax.text(.1,.5,'precision:',ha='left',va='center',transform=ax.transAxes)
    prec_disp = ax.text(.3,.5,'',ha='left',va='center',transform=ax.transAxes)
    # callbacks
    def on_button_press(ev):
      if ev.button == MouseButton.LEFT and ev.key is None:
        if ev.inaxes is play_toggler.axes: self.setrunning()
        elif ev.inaxes is level_ctrl.axes:
          if .45<ev.ydata<.55: return
          i = self.level+(+1 if ev.ydata>.55 else -1)
          if 0<=i<=level_max: setlevel(i)
    toolbar.canvas.mpl_connect('button_press_event',on_button_press)
    super().__init__(display,**ka)
