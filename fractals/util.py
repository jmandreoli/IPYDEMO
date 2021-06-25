# File:                 fractals/util.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Utilities for fractal display
#

import logging
logger = logging.getLogger(__name__)
from matplotlib.pyplot import figure, rcParams
from matplotlib.backend_bases import MouseButton
from matplotlib.patches import Rectangle
try: from myutil.ipywidgets import app, SimpleButton # so this works even if ipywidgets is not available
except: app = object

#==================================================================================================
class Selection:
#==================================================================================================
  def __init__(self,ax,callback=(lambda *a: None),min_size=1e-10,**ka):
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
class widget_player (app):
#==================================================================================================
  def __init__(self,master,fig_kw={},children=(),toolbar=()):
    from ipywidgets import BoundedIntText,Text,Label
    w_running = SimpleButton(icon='')
    w_level = BoundedIntText(0,min=0,max=0,layout=dict(width='1.6cm',padding='0cm'))
    w_precision = Text('',layout=dict(width='1.6cm',padding='0cm'))
    super().__init__(children,toolbar=(w_running,Label('level:'),w_level,Label('precision:'),w_precision,*toolbar))
    self.board = self.mpl_figure(**fig_kw)
    w_running.on_click(lambda b: master.set_running())
    w_level.observe(lambda c: master.set_level(c.new),'value')
    def set_running(b): w_running.icon = 'pause' if b else 'play'
    self.set_running = set_running
    def set_level(i,imax):
      with w_level.hold_trait_notifications(): w_level.max = imax; w_level.value = i
    self.set_level = set_level
    def set_precision(p): w_precision.value = str(p)
    self.set_precision = set_precision

#==================================================================================================
class mpl_player:
#==================================================================================================
  def __init__(self,master,tbsize=((.15,.8,1.4),.15),fig_kw={}):
    tbsize_ = sum(tbsize[0])
    figsize = fig_kw.pop('figsize',None)
    if figsize is None: figsize = rcParams['figure.figsize']
    figsize_ = list(figsize); figsize_[1] += tbsize[1]; figsize_[0] = max(figsize_[0],tbsize_)
    self.main = main = figure(figsize=figsize_,**fig_kw)
    r = tbsize[1],figsize[1]
    toolbar,self.board = main.subfigures(nrows=2,height_ratios=r)
    r = list(tbsize[0])
    r[2] += figsize_[0]-tbsize_
    g = dict(width_ratios=r,wspace=0.,bottom=0.,top=1.,left=0.,right=1.)
    axes = toolbar.subplots(ncols=3,subplot_kw=dict(xticks=(),yticks=(),navigate=False),gridspec_kw=g)
    # widget definition
    play_toogler = axes[0].text(.5,.5,'',ha='center',va='center',transform=axes[0].transAxes)
    axes[1].text(.1,.5,'level:',ha='left',va='center',transform=axes[1].transAxes)
    level_ctrl = axes[1].text(.6,.5,'0/',ha='left',va='center',transform=axes[1].transAxes)
    level_ctrl.current = 0,0
    axes[2].text(.1,.5,'precision:',ha='left',va='center',transform=axes[2].transAxes)
    prec_ctrl = axes[2].text(.3,.5,'',ha='left',va='center',transform=axes[2].transAxes)
    def on_key_press(ev):
      key = ev.key
      if ev.inaxes is not None and (key == 'left' or key == 'right'):
        i,imax = level_ctrl.current
        i += (+1 if key == 'right' else -1)
        if 0<=i<=imax: master.set_level(i)
    def on_button_press(ev):
      if ev.button == MouseButton.LEFT and ev.key is None and ev.inaxes is play_toogler.axes:
        master.set_running(); toolbar.canvas.draw_idle()
    toolbar.canvas.mpl_connect('key_press_event',on_key_press)
    toolbar.canvas.mpl_connect('button_press_event',on_button_press)
    def set_running(b): play_toogler.set(text='II' if b else '|>')
    self.set_running = set_running
    def set_level(i,imax): level_ctrl.set(text=f'{i}/{imax}'); level_ctrl.current = i,imax
    self.set_level = set_level
    def set_precision(p): prec_ctrl.set(text=str(p))
    self.set_precision = set_precision

  def _ipython_display_(self): return repr(self)
