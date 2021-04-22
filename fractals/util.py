# File:                 fractals/util.py
# Creation date:        2015-03-19
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Utilities for fractal display
#

import logging
logger = logging.getLogger(__name__)

#--------------------------------------------------------------------------------------------------
def MultizoomAnimation(ax,func=None,frames=None,**ka):
#--------------------------------------------------------------------------------------------------
  r"""
:param ax: matplotlib axes on which to display
:type ax: :class:`matplotlib.Axes` instance
:param func: a display function (see below)
:param frames: a generator function (see below)
:param ka: passed to :func:`matplotlib.FuncAnimation`

Displays a target (2-D object, typically a fractal) allowing navigation through multiple levels of zooming. For a given zooming level, the display is assumed dynamic, starting from a coarse precision level and refining progressively over time (typical of fractals).

- Function *frames* is passed a bounding box specification and is expected to return an iterator of frame informations needed to draw the subset of the target within this bounding box, at successive levels of precision. The iterator is enumerated at regular intervals in the animation as long as the zooming level is not changed, and resumed whenever the same zooming level is reselected. A bounding box spec is a pair (x-bounds,y-bounds) of pairs corresponding to the two opposite corners of the bounding box in data coordinates.

- Function *func* is passed a frame information (from the iterator returned by *frame*\), and is expected to draw the frame on *ax*\.

At any zooming level, the frame iteration can be interrupted/resumed by pressing the space key.
  """
  from matplotlib.animation import FuncAnimation
  def Func(args):
    if args is None: return (selection.rec,)
    (n,v),newprec = args
    txt.set_text(str(n))
    txt.set_color('k' if newprec else 'r')
    return (selection.rec,txt)+func(v)
  def Frames():
    level = None
    while True:
      if selection.bbox is None:
        newlev = level!=selection.level
        level = selection.level
        seq = stack[level]
        newprec = seq.step()
        yield seq.value,newprec if newprec or newlev else None
      else:
        yield None
  def new_zoom(level,bounds):
    assert level<=len(stack)
    del stack[level:]
    it = frames(bounds)
    n = stack[-1].value[0] if level else 0 # initial precision of new zoom level equals that of parent
    for _ in range(n): next(it)
    stack.append(State(enumerate(it,n)))
  def toggle_freeze(ev):
    if ev.artist != txt: return
    stack[selection.level].toggle()
  try: ax.figure.canvas.toolbar.setVisible(False)
  except: pass
  stack = []
  txt = ax.text(.001,.999,'',ha='left',va='top',backgroundcolor='w',color='k',fontsize='xx-small',transform=ax.transAxes,picker=True)
  selection = ZoomSelection(ax,newzoom=new_zoom)
  ax.figure.canvas.mpl_connect('pick_event',toggle_freeze)
  return FuncAnimation(ax.figure,func=Func,frames=Frames,**ka)

#==================================================================================================
class ZoomSelection:
#==================================================================================================
  r"""
:param ax: a matplotlib axes
:param newzoom: a callback function with two arguments (default: do nothing).

Objects of this class manage a stack of zoom levels on axes *ax*. A zoom level is defined by a boundary specification (a pair of pairs: x-bounds and y-bounds in data coordinates). A new zoom level is created on top of the current level in the stack by user selection of a rectangle on the axes, using the mouse. Function *newzoom* is invoked with each newly created zoom level (its level and bounds are passed as arguments). Pressing the arrow keys on the keyboard allows navigation through the zoom level stack (up or right arrow to go up the stack, down or left arrow to go down).

Attributes:

.. attribute:: rec

   The rectangle (:class:`matplotlib.patch.Rectangle` instance) for zoom level selection. Visible at all levels of zooming except the top one, where it is visible only when selection is ongoing.

.. attribute:: msize

   Minimal width or height for the rectangle to be admissible selection.

.. attribute:: txt

   A text widget (:class:`matplotlib.text.Text` instance) to display the zoom level.

.. attribute:: stack

   The stack of boundary specifications for each zoom level. At initialisation, the boundary of *ax* are used.

.. attribute:: level

   The current zoom level, as an index in the :attr:`stack`\.

.. attribute:: bbox

   Set to :const:`None` when no selection is active, otherwise, set to the current selection (corners of the boundary rectangle).

Methods:
  """

#--------------------------------------------------------------------------------------------------
  def __init__(self,ax,newzoom=(lambda *a: None),**ka):
#--------------------------------------------------------------------------------------------------
    from matplotlib.patches import Rectangle
    ax.figure.canvas.mpl_connect('button_press_event',self.start)
    ax.figure.canvas.mpl_connect('button_release_event',self.stop)
    ax.figure.canvas.mpl_connect('motion_notify_event',self.updt)
    ax.figure.canvas.mpl_connect('key_press_event',self.xlevel)
    self.rec = ax.add_patch(Rectangle((0,0),width=0,height=0,alpha=.4,color='k',visible=False,**ka))
    self.msize = 1e-10
    self.txt = ax.text(.999,.999,'0',ha='right',va='top',backgroundcolor='w',color='k',fontsize='xx-small',transform=ax.transAxes)
    bounds = ax.get_xlim(),ax.get_ylim()
    self.stack = [bounds]
    self.level = 0
    self.bbox = None
    self.newzoom = newzoom
    newzoom(0,bounds)

#--------------------------------------------------------------------------------------------------
  def start(self,ev):
    r"""
:param ev: a GUI event
:type ev: :class:`matplotlib.Event` instance

Initiates a rectangle capture when button 1 is pressed.
    """
#--------------------------------------------------------------------------------------------------
    if ev.inaxes != self.rec.axes or ev.button != 1 or self.bbox is not None: return
    p = ev.xdata, ev.ydata
    self.bbox = [p,p]
    self.rec.set(xy=p,width=0,height=0,visible=True)

#--------------------------------------------------------------------------------------------------
  def updt(self,ev):
    r"""
:param ev: a GUI event
:type ev: :class:`matplotlib.Event` instance

Updates the rectangle capture while button 1 is pressed and the mouse moves around.
    """
#--------------------------------------------------------------------------------------------------
    if ev.inaxes != self.rec.axes or self.bbox is None: return
    p = self.bbox[0]
    p1 = self.bbox[1] = ev.xdata, ev.ydata
    self.rec.set(width=p1[0]-p[0],height=p1[1]-p[1])

#--------------------------------------------------------------------------------------------------
  def stop(self,ev):
    r"""
:param ev: a GUI event
:type ev: :class:`matplotlib.Event` instance

Finalises the rectangle capture when button 1 is released.
    """
#--------------------------------------------------------------------------------------------------
    if ev.inaxes != self.rec.axes or ev.button != 1 or self.bbox is None: return
    p,p1 = self.bbox
    self.bbox = None
    if abs(p1[0]-p[0])<self.msize or abs(p1[1]-p[1])<self.msize: return
    bounds = tuple(sorted((p[0],p1[0]))), tuple(sorted((p[1],p1[1])))
    self.level += 1
    self.txt.set_text(str(self.level))
    del self.stack[self.level:]
    self.stack.append(bounds)
    self.rec.set(visible=False)
    self.newzoom(self.level,bounds)

#--------------------------------------------------------------------------------------------------
  def xlevel(self,ev):
    r"""
:param ev: a GUI event
:type ev: :class:`matplotlib.Event` instance

Navigates across the zoom levels.
    """
#--------------------------------------------------------------------------------------------------
    if self.bbox is not None: return
    showrec = True
    if ev.key in ('up','right'):
      if self.level<len(self.stack)-1:
        self.level += 1
        if self.level == len(self.stack)-1: showrec = False # top of stack
      else: return
    elif ev.key in ('down','left'):
      if self.level>0: self.level -= 1
      else: return
    else: return
    if showrec:
      (p00,p10),(p01,p11) = self.stack[self.level+1]
      self.rec.set(xy=(p00,p01),width=p10-p00,height=p11-p01)
    self.rec.set(visible=showrec)
    self.txt.set_text(str(self.level))

#==================================================================================================
class State:
  r"""
An object of this class is a simple state machine defined by an iterator *it*, passed as argument to its constructor. The state of this machine is available as attribute :attr:`value`. Method :meth:`step` sets the state to the next element of *it*, if the iterator is not exhausted and the machine is not interrupted (otherwise, the state is unchanged). The machine can be interrupted/resumed using method :meth:`toggle`.
  """
#==================================================================================================
  def __init__(self,it,running=True):
    running = running
    alive = True
    self.value = None
    def toggle():
      nonlocal running
      if alive: running = not running
      return running
    self.toggle = toggle
    def step():
      nonlocal running, alive
      if running:
        try:
          self.value = next(it)
          return True
        except StopIteration:
          alive = running = False
      return False
    self.step = step
