# File:                 sudoku/core.py
# Creation date:        2025-08-15
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Sudoku problem generation and solving
#

from __future__ import annotations
import logging;logger = logging.getLogger(__name__)
from typing import Any, Union, Callable, Iterable, Mapping, Tuple

import mip
from functools import cached_property
from numpy import ndarray,array,ones,where,random,sqrt,eye
from time import perf_counter

__all__ = 'SolveError', 'solve', 'Sudoku'

def _generic_constraints(N):
  # constrains *X* to satisfy the generic Sudoku rules
  L = [sel for p in range(N) for q in range(N) for sel in ((p,q,...),(p,...,q),(...,p,q))]
  N_ = round(sqrt(N))
  L.extend((slice(i,i+N_),slice(j,j+N_),k) for i in range(0,N,N_) for j in range(0,N,N_) for k in range(N))
  return lambda X: (mip.xsum(X[sel].flat)==1 for sel in L)

def _partial_constraints(N,except_at=None):
  # constrains *X* to coincide with a partial *grid*, except possibly at one cell
  if except_at is None:
    return lambda X,grid: (v==1 for k in range(N) for v in X[grid==k,k])
  def g(X,grid):
    v_ = X[except_at]; yield v_==0
    yield from (v==1 for k in range(N) for v in X[grid==k,k] if v is not v_)
  return g

def _different_from_constraints(N):
  # constrains X be different from any one of a list of complete *grids*
  N_ = N*N-1
  return lambda X,grids: (mip.xsum(v for k in range(N) for v in X[grid==k,k])<=N_ for grid in grids)

def _extract_solution(X):
  # extracts the solution (complete grid) from a solved system *X*
  return array([[next(k for k,v in enumerate(Xij) if v.x==1) for Xij in Xi] for Xi in X])

#==========================================================================
SolveError = type('SolveError',(Exception,),{})
def solve(constraints,N=9,M=mip.Model()):
  r"""
Solves a Sudoku problem under a set of constraints. The problem is expressed as a MIP.
There is one binary variable for each triple of a row (out of 9), a column (out of 9) and an allowed value (out of 9), hence a 3-way tensor of 729 MIP variables.
The Sudoku rules impose 324 generic constraints (not independent), to which *constraints* are added.

:param constraints: a callable which takes the tensor of MIP variables and returns an iterable of constraints
:param N: dimension of the problem
  """
#==========================================================================
  previous = []; elapsed = 0
  all_constraints = [_generic_constraints(N),constraints,(lambda X,g=_different_from_constraints(N): g(X,previous))]
  while True:
    M.clear(); M.verbose = 0
    X = M.add_var_tensor((N,N,N),'X',var_type=mip.BINARY)
    for g in all_constraints:
      for constr in g(X): M.add_constr(constr)
    t = perf_counter(); status = M.optimize(); elapsed += perf_counter()-t
    if status is mip.OptimizationStatus.OPTIMAL:
      grid = _extract_solution(X)
      previous.append(grid)
      yield grid,elapsed
    elif status is mip.OptimizationStatus.INFEASIBLE: return
    else: raise SolveError(status,elapsed)

#==========================================================================
class Sudoku:
  r"""
Instances of this class are possibly partially filled Sudoku grids.
The grid is a :class:`numpy:ndarray` of :class:`int` between -1 and N where N is a perfect square (9,16,25...).

:param grid: the grid or an integer, denoting the empty grid of that dimension (default 9)
:param solved: time to solve (in ms)
:param source: mask of initial cells (for solved grids)
:param props: a jsonable dictionary
  """
#==========================================================================

#--------------------------------------------------------------------------
  def __init__(self,grid=9,solved=None,source=None,props:dict[str,Any]|None=None):
#--------------------------------------------------------------------------
    if isinstance(grid,int): N = grid; grid = -ones((N,N),dtype=int) # empty grid
    else:
      grid = array(grid,dtype=int); N = grid.shape[0]
      assert grid.shape==(N,N) and (-1<=grid).all() and (grid<=N).all()
    self.N = N; N_ = round(sqrt(N)); assert N_*N_ == N
    self.grid = grid
    self.partial_constraints = lambda X,g=_partial_constraints(N): g(X,grid)
    if props is None: props = {}
    else: assert isinstance(props,dict) and jsonable(props)
    self.props = props
    self.solved = self.source = None
    if solved is None: assert source is None; source = grid >= 0
    else: assert isinstance(solved,float) and solved>0 and isinstance(source,ndarray) and source.shape==grid.shape and source.dtype==bool
    self.solved,self.source,self.density = solved,source,float(source.sum()/source.size)
    # display name
    s = f'density: {self.density:.3f}'
    if solved is not None: s = '; '.join((s,f'solved:{1000*solved:.1f}ms'))
    s = '; '.join((s,*(f'{k}:{v!r}' for k,v in props.items())))
    self._repr = f'Sudoku[{s}]'
  def __repr__(self): return self._repr

#--------------------------------------------------------------------------
  def solve(self,check=False):
    r"""
Solves this instance. Returns a new instance whose cells are all filled.

:param check: whether to check that the solution is correct and unique
    """
#--------------------------------------------------------------------------
    if self.solved is not None: return self
    solutions = solve(self.partial_constraints)
    grid,elapsed = next(solutions)
    source = self.source
    if check:
      assert (grid[source] == self.grid[source]).all() # sanity check
      try: next(solutions)
      except StopIteration: pass
      else: raise Exception('Grid has more than one solution')
    return Sudoku(grid,solved=elapsed,source=source,props=self.props)

#--------------------------------------------------------------------------
  @cached_property
  def _repr_html(self):
    r"""A html representation of the grid for IPython display."""
#--------------------------------------------------------------------------
    from lxml.html import builder as E, tostring
    pos2tag = {-1:''}|{k:str(k+1) for k in range(self.N)}
    FGBG = {q:f'color:{fg};background-color:{bg};' for q,fg,bg in ((False,'blue','white'),(True,'black','lightgray'))}
    LW = {False:'1px',True:'4px'}
    style_c = 'width:.5cm;height:.5cm;text-align:center;vertical-align:middle;border-style:solid;border-color:black;'
    style_f = 'background-color:black;color:white;text-align:center;vertical-align:middle;font-size:xx-small;'
    def style(i,j):
      fgbg = FGBG[self.source[i,j]]; top,right,bottom,left = (LW[q%3==0] for q in (i,j+1,i+1,j))
      return style_c+fgbg+f'border-width: {top} {right} {bottom} {left};'
    table = E.TABLE(
      E.TBODY(*(
        E.TR(*(
          E.TD(pos2tag[k],style=style(i,j)) for j,k in enumerate(r)
        )) for i,r in enumerate(self.grid))
      ),
      E.TFOOT(E.TR(E.TD(str(self),colspan='9',style=style_f)))
    )
    return tostring(table,encoding='unicode')
  def _repr_html_(self): return self._repr_html

#--------------------------------------------------------------------------
  @staticmethod
  def generate(N:int=9,target_density:float=0.,check:bool=True,step:Callable[[ndarray,int,int,int],None]=(lambda *a:None),**ka):
    r"""
Generates a random Sudoku instance. Starts with a full one then walks through all the cell, removing them when possible, until *target_density* is reached (or all the cells have been processed).

:param N: dimension of the grid to generate
:param target_density: the target density (between 0. and 1.)
:param check: whether to check that the instance has a unique solution
:param step: called after each step in the sequence of cell removals
    """
#--------------------------------------------------------------------------
    solution = solve((lambda X: (v==1 for v in X[0,eye(N,dtype=bool)])),N) # alternative: (lambda X:())
    for _ in range(random.randint(0,4)): next(solution)
    grid,_ = next(solution)
    N_sqr = N*N; d = 0; dmin = round((1.-target_density)*N_sqr)
    for i,j in (divmod(int(n),N) for n in random.permutation(N_sqr)):
      k = int(grid[i,j]); assert k>=0 # sanity check
      step(grid,i,j,k)
      g = _partial_constraints(N,except_at=(i,j,k)) # alternative: consistent with grid but different from *initial* grid
      try: next(solve((lambda X: g(X,grid)),N))
      except (SolveError,StopIteration):
        grid[i,j] = -1; d += 1
        if d>=dmin: break
    q = random.permutation(N)
    grid = where(grid==-1,-1,q[grid])
    level = '?'
    s = Sudoku(grid,props={'level':level,**ka})
    if check: s.solve(check=True)
    return s

#--------------------------------------------------------------------------
def jsonable(v):
# --------------------------------------------------------------------------
  import json
  try: json.dumps(v)
  except: return False
  else: return True
