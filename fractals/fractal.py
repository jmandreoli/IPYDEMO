import logging
logger = logging.getLogger(__name__)

#----------------------------------------------------------------------------------------------------
def FractalAnimation(ax,func=None,frames=None,**ka):
#----------------------------------------------------------------------------------------------------
  r"""
:param ax: matplotlib axes on which to display
:type ax: :class:`matplotlib.Axes` instance
:param func: a display function (see below)
:param frames: a generator function (see below)
:param ka: passed to :func:`matplotlib.FuncAnimation`

Displays an object (target, typically a fractal) allowing navigation through multiple levels of zooming. For a given zooming level, the display is assumed dynamic, starting from a coarse precision level and refining progressively over time (typical of fractals).

* Function *frames* is passed a boundary specification and is expected to return an iterator of frame informations needed to draw the subset of the target within this boundary at successive levels of precision. The iterator is enumerated at regular intervals in the animation as long as the zooming level is not changed, and resumed whenever the same zooming level is reselected. A boundary spec is a pair of pairs (the x-bounds and the y-bounds in data coordinates).

* Function *func* is passed a frame information (from the iterator returned by *frame*\) and a boolean flag, and is expected to draw the frame on *ax*\. It is called at each new precision level with the flag set to :const:`False`, and when the zooming level changes with the flag is set to :const:`True`.
  """
  from matplotlib.animation import FuncAnimation
  def forever(k,seq):
    n = 0; v = None
    while True:
      try: v = next(seq); n += 1
      except StopIteration: pass
      yield k,n,v
  def Func(args,cur=[-1,0]):
    if args is None: return (selection.rec,)
    else:
      k,n,v = args
      if k!= cur[0]: cur[:] = k,n; i = True
      elif n!= cur[1]: cur[1] = n; i = False
      else: return()
      txt.set_text(str(n))
      return (selection.rec,txt)+func(v,interrupt=i)
  def Frames():
    def gc(k): del stack[k:]
    selection.gc = gc
    stack = []
    while True:
      if selection.bbox is None:
        k,K = selection.level, len(stack)
        if K<k:
          assert k==K+1
          seq = forever(K,frames(selection.stack[K]))
          stack.append(seq)
        else: seq = stack[k-1]
        yield next(seq)
      else:
        yield None
  try: ax.figure.canvas.toolbar.setVisible(False)
  except: pass
  selection = Selection(ax)
  txt = ax.text(.001,.999,'',ha='left',va='top',backgroundcolor='w',color='k',fontsize='xx-small',transform=ax.transAxes)
  return FuncAnimation(ax.figure,func=Func,frames=Frames,**ka)

#----------------------------------------------------------------------------------------------------
class Selection:
#----------------------------------------------------------------------------------------------------
  r"""
Objects of this class manage a stack of zoom levels on some axes. A zoom level is defined by a boundary specification (a pair of pairs: x-bounds and y-bounds in data coordinates). A new zoom level is created on top of the current level in the stack by user selection of a rectangle on the axes, using the mouse. Pressing the arrow keys on the keyboard allows navigation through the zoom level stack (up or right arrow to go up the stack, down or left arrow to go down).

Attributes:

.. attribute:: rec

   The rectangle (:class:`matplotlib.patch.Rectangle` instance) for zoom level selection. Visible at all levels of zooming except the top one, where it is visible only when selection is ongoing.

.. attribute:: txt

   A text widget (:class:`matplotlib.text.Text` instance) to display the zoom level.

.. attribute:: stack

   The stack of boundary specifications for each zoom level. At initialisation, the boundary of the the axes are used.

.. attribute:: level

   The current zoom level, as an index in the :attr:`stack`\.

.. attribute:: bbox

   Set to :const:`None` when no selection is active, otherwise, set to the current selection (corners of the boundary rectangle).

.. attribute:: gc

   A callback function with one argument, which is called with each newly created zoom level (its index is passed as argument). This allows for garbage collection of the zoom levels above the current one, which are discarded by the newly created one.

Methods:
  """

  def __init__(self,ax,gc=(lambda l: None),**ka):
    from matplotlib.patches import Rectangle
    ax.figure.canvas.mpl_connect('button_press_event',self.start)
    ax.figure.canvas.mpl_connect('button_release_event',self.stop)
    ax.figure.canvas.mpl_connect('motion_notify_event',self.updt)
    ax.figure.canvas.mpl_connect('key_press_event',self.xlevel)
    self.rec = ax.add_patch(Rectangle((0,0),width=0,height=0,alpha=.4,color='k',visible=False,**ka))
    self.txt = ax.text(.999,.999,'1',ha='right',va='top',backgroundcolor='w',color='k',fontsize='xx-small',transform=ax.transAxes)
    self.stack = [(ax.get_xlim(),ax.get_ylim())]
    self.level = 1
    self.bbox = None
    self.gc = gc

  def start(self,ev):
    r"""
:param ev: a GUI event
:type ev: :class:`matplotlib.Event` instance

Initiates a rectangle capture when button 1 is pressed.
    """
    if ev.inaxes != self.rec.axes or ev.button != 1 or self.bbox is not None: return
    p = ev.xdata, ev.ydata
    self.bbox = [p,p]
    self.rec.set_xy(p)
    self.rec.set_visible(True)

  def updt(self,ev):
    r"""
:param ev: a GUI event
:type ev: :class:`matplotlib.Event` instance

Updates the rectangle capture while button 1 is pressed and the mouse moves around.
    """
    if ev.inaxes != self.rec.axes or self.bbox is None: return
    p = self.bbox[0]
    p1 = self.bbox[1] = ev.xdata, ev.ydata
    self.rec.set_width(p1[0]-p[0])
    self.rec.set_height(p1[1]-p[1])

  def stop(self,ev):
    r"""
:param ev: a GUI event
:type ev: :class:`matplotlib.Event` instance

Finalises the rectangle capture when button 1 is released.
    """
    if ev.inaxes != self.rec.axes or ev.button != 1 or self.bbox is None: return
    p,p1 = self.bbox
    bounds = tuple(sorted((p[0],p1[0]))), tuple(sorted((p[1],p1[1])))
    del self.stack[self.level:]
    self.gc(self.level)
    self.stack.append(bounds)
    self.level += 1
    self.txt.set_text(str(self.level))
    self.bbox = None

  def xlevel(self,ev):
    r"""
:param ev: a GUI event
:type ev: :class:`matplotlib.Event` instance

Navigates across the zoom levels.
    """
    if self.bbox is not None: return
    if ev.key in ('up','right'):
      if self.level<len(self.stack): self.level += 1
    elif ev.key in ('down','left'):
      if self.level>1: self.level -= 1
    else: return
    if self.level<len(self.stack):
      (p00,p10),(p01,p11) = self.stack[self.level]
      self.rec.set_xy((p00,p01))
      self.rec.set_width(p10-p00)
      self.rec.set_height(p11-p01)
      self.rec.set_visible(True)
    else: self.rec.set_visible(False)
    self.txt.set_text(str(self.level))
