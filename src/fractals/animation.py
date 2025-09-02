from typing import Any, Union, Callable, Iterable, Mapping, Sequence, Tuple
from matplotlib import rcParams, get_backend
from matplotlib.pyplot import figure
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
try: from myutil.ipywidgets import app, SimpleButton # so this works even if ipywidgets is not available
except: app = object

#==================================================================================================
class BaseControlledAnimation (FuncAnimation):
  r"""
An instance of this class controls the exploration of a fractal.

:param display: a function which, given a zoom level and possibly its new specification, displays it on the board
  """
#==================================================================================================

  def __init__(self,display:Callable[[int,Any],None],**ka):
    def frames():
      self.select(None); self.set_running(False); yield None
      while True: yield self.level
    self.level = -1
    super().__init__(self.board,(lambda i: None if i is None else self.show_precision(display(i))),frames,init_func=(lambda: None),repeat=False,cache_frame_data=False,**ka)

  def set_running(self,b:bool):
    r"""Sets the running state of the animation to *b*."""
    self.running = b
    (self.resume if b else self.pause)()
    self.show_running(b)
  def toggle_running(self): self.set_running(not self.running)

  def show_running(self,b:bool):
    r"""Shows the current running state as *b*. This implementation raises an error."""
    raise NotImplementedError()

  def show_precision(self,p:int):
    r"""Shows the current precision as *p*. This implementation raises an error."""
    raise NotImplementedError()

  def select(self,bounds:Tuple[Tuple[float,float],Tuple[float,float]]|None):
    r"""Pushes a new level in the animation at the current level plus one. This implementation raises an error."""
    raise NotImplementedError()

#==================================================================================================
class IPYControlledAnimation (BaseControlledAnimation,app):
  r"""
This class refines :class:`player_base` for backends which support :mod:`ipywidgets`.

:param displayer: passed the board figure as well as the selector on that board, returns the *display* argument of the superclass
:param resolution: the (constant) resolution for all the zoom level (total number of pixels to display)
  """
#==================================================================================================
  def __init__(self,display:Callable[[int,Any],None],resolution:int=None,fig_kw={},toolbar=(),**ka):
    from ipywidgets import BoundedIntText,IntText,Label
    def select(bounds_):
      i = self.level+1
      w_level.active = False
      w_level.max = i; w_level.value = i
      set_level(i,(resolution,bounds_))
      w_level.active = True
    def show_running(b): w_play_toggler.icon = 'pause' if b else 'play'
    def show_precision(p): w_precision.value = p
    self.select = select
    self.show_precision = show_precision
    self.show_running = show_running
    def set_level(i,new=None):
      self.level = i
      w_precision.value = display(i,new)
      board.canvas.draw_idle()
    # global design and widget definitions
    w_play_toggler = SimpleButton(icon='')
    w_level = BoundedIntText(0,min=0,max=0,layout=dict(width='1.6cm',padding='0cm'))
    w_level.active = True
    w_precision = IntText(0,disabled=True,layout=dict(width='1.6cm',padding='0cm'))
    app.__init__(self,toolbar=(w_play_toggler,Label('level:'),w_level,Label('precision:'),w_precision,*toolbar))
    self.board = board = self.mpl_figure(**fig_kw)
    # callbacks
    w_play_toggler.on_click(lambda b: self.toggle_running())
    w_level.observe((lambda c: (set_level(c.new) if w_level.active else None)),'value')
    super().__init__(display,**ka)

#==================================================================================================
class MPLControlledAnimation (BaseControlledAnimation):
  r"""
This class refines :class:`player_base` for backends which do not support :mod:`ipywidgets`.

:param displayer: passed the board figure as well as the selector on that board, returns the *display* argument of the superclass
:param resolution: the (constant) resolution for all the zoom level (total number of pixels to display)
  """
#==================================================================================================
  def __init__(self,display:Callable[[int,Any],None],resolution:int=None,fig_kw={},tbsize=((.15,.8,.15,1.4),.15),**ka):
    level_max = 0
    def select(bounds_):
      nonlocal level_max
      level_max = i = self.level+1
      set_level(i,(resolution,bounds_))
    def show_running(b): play_toggler.set(text='II' if b else r'$\blacktriangleright$'); toolbar.canvas.draw_idle()
    def show_precision(p): prec_disp.set(text=str(p)); toolbar.canvas.draw_idle()
    self.select = select
    self.show_running = show_running
    self.show_precision = show_precision
    def set_level(i,new=None):
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
    toolbar,self.board = main.subfigures(nrows=2,height_ratios=r)
    r = list(tbsize[0])
    r[3] += figsize_[0]-tbsize_
    g = {'width_ratios':r,'wspace':0.,'bottom':0.,'top':1.,'left':0.,'right':1.}
    axes = toolbar.subplots(ncols=4,subplot_kw={'xticks':(),'yticks':(),'navigate':False},gridspec_kw=g)
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
        if ev.inaxes is play_toggler.axes: self.toggle_running()
        elif ev.inaxes is level_ctrl.axes:
          if .45<ev.ydata<.55: return
          i = self.level+(+1 if ev.ydata>.55 else -1)
          if 0<=i<=level_max: set_level(i)
    toolbar.canvas.mpl_connect('button_press_event',on_button_press)
    super().__init__(display,**ka)

def ControlledAnimation(*a,**ka): return IPYControlledAnimation(*a,**ka) if get_backend()=='widget' else MPLControlledAnimation(*a,**ka)
