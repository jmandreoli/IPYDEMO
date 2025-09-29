# File:                 sudoku/core.py
# Creation date:        2025-08-15
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Tools for Sudoku problem management
#

from __future__ import annotations
import logging;logger = logging.getLogger(__name__)
from typing import Any, Union, Callable, Iterable, Mapping, Tuple

from collections.abc import MutableSequence
from traitlets import Instance
from .core import Sudoku

#--------------------------------------------------------------------------
def dashboard(dataset:MutableSequence[Sudoku]):
  r"""A widget to play with a dataset of problems."""
#--------------------------------------------------------------------------
  from ipywidgets import Dropdown,Output,HBox,VBox,Button,Tab,FloatSlider,Checkbox,IntProgress
  from IPython.display import clear_output, display
  def W(w): w.layout.width = 'auto'; w.style.description_width = 'auto'; return w
  def setoptions(i=0,deactivate=False):
    nonlocal active
    try: active = not deactivate; w_sample.options = [('',None),*((f'{i}-{s}',s) for i,s in enumerate(dataset,1))]; w_sample.index = i
    finally: active = True
  def setval(s):
    if active: w.value = s; w_sol.disabled = s is None
  def message(*x):
    with w_out: print(*x)
  w = VBox((
    w_tab:=Tab((
      HBox((
        w_sample:=Dropdown(value=None,layout={'min-width':'10cm'}),
        w_remove:=W(Button(description='remove',layout={'display':'none'}))
      )),
      HBox((
        w_den:=FloatSlider(min=0,max=1,step=1/81,tooltip='Target density',layout={'min-width':'10cm'}),
        w_check:=W(Checkbox(value=True,tooltip='Whether to check the generated solution (recommended)')),
        w_generated:=W(Button(description='generate')),
        w_progress:=IntProgress(min=0,max=81,value=0,layout={'display':'none'}),
        w_save:=W(Button(description='save',layout={'display':'none'}))
      ))
    )),
    HBox((w_sol:=W(Button(description='solution',disabled=True)),w_solx:=W(Button(icon='close',layout={'display':'none'})))),
    w_out:=Output(layout={'min-width':'10cm','min-height':'10cm'})
  ))
  w_tab.titles = 'Repository','Generator'
  w.add_traits(value=Instance(Sudoku,allow_none=True))
  w_generated.add_traits(value=Instance(Sudoku,allow_none=True))
  w.value = w_generated.value = w_sample.value = None
  w.observe((lambda c: from_w(c.new)),'value')
  w_tab.observe((lambda c: setval(w_sample.value if c.new==0 else w_generated.value) if active else None),'selected_index')
  w_sample.observe((lambda c: setattr(w_remove.layout,'display','none' if c.new is None else '')),'value')
  w_sample.observe((lambda c: setval(c.new)),'value')
  w_generated.observe((lambda c: setval(c.new)),'value')
  w_generated.on_click(lambda b: gen())
  w_sol.on_click(lambda b: sol())
  w_solx.on_click(lambda b: solx())
  w_save.on_click(lambda b: save())
  w_remove.on_click(lambda b: remove())
  def from_w(s):
    w_solx.layout.display = 'none'
    with w_out: clear_output(wait=True); display(s)
  def sol():
    exc = None
    if w.value is None: sol = None
    else:
      try: sol = w.value.solve()
      except Exception as e: exc = e
    with w_out:
      clear_output(wait=True)
      if exc is None: display(sol); w_solx.layout.display = ''
      else: display(w.value); print(exc)
  def solx():
    with w_out: clear_output(wait=True); display(w.value); w_solx.layout.display = 'none'
  def gen():
    w_save.layout.display = 'none'
    w_progress.layout.display = ''; w_progress.value = 0
    w_generated.disabled = True
    try: s = Sudoku.generate(9,w_den.value,check=w_check.value,step=lambda *a:setattr(w_progress,'value',w_progress.value+1))
    except Exception as e: message('Generation failed:',e)
    else: w_generated.value = s; w_save.layout.display = '' if w_check.value else 'none'
    w_generated.disabled = False
    w_progress.layout.display = 'none'
    w_save.layout.display = 'none' if w_generated.value is None else ''
  def save(): i = w_sample.index; dataset.append(w_generated.value); message('save complete'); setoptions(i,True); w_save.layout.display = 'none'
  def remove(): i = w_sample.index; assert i>0; dataset.remove(w_sample.value); message('remove complete'); setoptions(i-1); w_remove.layout.display = 'none' if w_sample.value is None else ''
  active = True
  message(None)
  setoptions()
  return w
