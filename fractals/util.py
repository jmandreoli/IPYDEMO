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

- Function *func* is passed a frame information (from the iterator returned by *frame*\) and a boolean flag, and is expected to draw the frame on *ax*\. It is called at each new precision level with the flag set to :const:`False`, and when the zooming level changes, with the flag is set to :const:`True`.

At any zooming level, the frame iteration can be interrupted/resumed by pressing the space key.
  """
  from matplotlib.animation import FuncAnimation
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
    while True:
      if selection.bbox is None:
        k,K = selection.level, len(stack)
        if K<=k:
          assert k==K
          seq = Forever((k,n,v) for n,v in enumerate(frames(selection.stack[k]),1))
          stack.append(seq)
        else: seq = stack[k]
        txt.set_color('k' if seq.running else 'r')
        yield next(seq.flow)
      else:
        yield None
  try: ax.figure.canvas.toolbar.setVisible(False)
  except: pass
  stack = []
  selection = Selection(ax)
  txt = ax.text(.001,.999,'',ha='left',va='top',backgroundcolor='w',color='k',fontsize='xx-small',transform=ax.transAxes)
  def freeze(ev):
    if ev.key != ' ': return
    stack[selection.level].toggle()
  ax.figure.canvas.mpl_connect('key_press_event',freeze)
  return FuncAnimation(ax.figure,func=Func,frames=Frames,**ka)

#==================================================================================================
class Selection:
#==================================================================================================
  r"""
Objects of this class manage a stack of zoom levels on some axes. A zoom level is defined by a boundary specification (a pair of pairs: x-bounds and y-bounds in data coordinates). A new zoom level is created on top of the current level in the stack by user selection of a rectangle on the axes, using the mouse. Pressing the arrow keys on the keyboard allows navigation through the zoom level stack (up or right arrow to go up the stack, down or left arrow to go down).

Attributes:

.. attribute:: rec

   The rectangle (:class:`matplotlib.patch.Rectangle` instance) for zoom level selection. Visible at all levels of zooming except the top one, where it is visible only when selection is ongoing.

.. attribute:: msize

   Minimal width or height of the rectangle

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

#--------------------------------------------------------------------------------------------------
  def __init__(self,ax,gc=(lambda l: None),**ka):
#--------------------------------------------------------------------------------------------------
    from matplotlib.patches import Rectangle
    ax.figure.canvas.mpl_connect('button_press_event',self.start)
    ax.figure.canvas.mpl_connect('button_release_event',self.stop)
    ax.figure.canvas.mpl_connect('motion_notify_event',self.updt)
    ax.figure.canvas.mpl_connect('key_press_event',self.xlevel)
    self.rec = ax.add_patch(Rectangle((0,0),width=0,height=0,alpha=.4,color='k',visible=False,**ka))
    self.msize = 1e-10
    self.txt = ax.text(.999,.999,'0',ha='right',va='top',backgroundcolor='w',color='k',fontsize='xx-small',transform=ax.transAxes)
    self.stack = [(ax.get_xlim(),ax.get_ylim())]
    self.level = 0
    self.bbox = None
    self.gc = gc

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
    self.rec.set_xy(p)
    self.rec.set_visible(True)

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
    self.rec.set_width(p1[0]-p[0])
    self.rec.set_height(p1[1]-p[1])

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
    self.gc(self.level)
    self.stack.append(bounds)

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
    self.rec.set_visible(showrec)
    self.txt.set_text(str(self.level))

#==================================================================================================
class Forever:
  r"""
An object of this class allows to control an iterator *it*, passed as argument to its constructor. The controlled iterator, available as attribute :attr:`flow`, enumerates the elements of *it* except that

- when *it* is exhausted, its last value is indefinitely repeated

- when this object is interrupted, *it* is untouched and the last value extracted from it is repeated until this object is resumed.

Use method :meth:`toggle` to interrupt/resume the object.
  """
#==================================================================================================
  def __init__(self,it,running=True):
    self.running = running
    def flow():
      a = next(it)
      yield a
      while True:
        if self.running: a = next(it,a)
        yield a
    self.flow = flow()
  def toggle(self): self.running = not self.running
