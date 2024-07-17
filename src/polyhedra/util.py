# File:                 polyhedra/util.py
# Creation date:        2022-10-01
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              some utilities on graph
#

from __future__ import annotations
from typing import Any, Union, Callable, Iterable, Generator, Mapping, Tuple, List, Optional, Any
import mip
from collections import defaultdict
from numpy import argmax, random

__all__ = 'colouring', 'PolyhedronSpec'

def colouring(N:Iterable[int],R:Iterable[Iterable[int]],*init:Iterable[Tuple[int,int]])->Generator[Tuple[int,Mapping[int,int]]]:
  r"""
Enumerates minimal solutions to a colouring problem on a set of nodes and a set of clusters (of nodes). A solution is a pair of an assignment of a colour to each node so that any two nodes in the same cluster have different colours. A minimal solution is a solution using a minimal number of colours.

A solution is given as a mapping of each node to a colour. To respect the constraint with :math:`C` colours, we must have

.. math::

   \begin{equation*}
   \max_{r\in R}|r| \;\;\leq\;\; C \;\;\leq\;\; |N|
   \end{equation*}

This is solved by MILP.

* Variables: one binary mip-variable :math:`x_{nc}` for each node :math:`n` and colour :math:`c`, specifying whether node :math:`n` has colour :math:`c`.
* Each node :math:`n` has exactly one colour: :math:`\sum_cx_{nc}=1`
* For each cluster :math:`r` and each colour :math:`c`, at most one node in :math:`r` has colour :math:`c`: :math:`\sum_{n\in r}x_{nc}\leq1`

:param N: the set of nodes
:param R: the set of clusters
:param init: an initialisation of some nodes as a list of node-colour pairs
:return: a pair of the total number of colours used and a solution
  """
  M = mip.Model()
  for C in range(max(len(r) for r in R),len(N)+1):
    sols = []
    while True:
      M.clear()
      # create a binary variable for each colour and each node:
      lvars = {n:[M.add_var(var_type=mip.BINARY) for _ in range(C)] for n in N}
      # force current solution to be distinct from all previous ones:
      for s in sols: M += mip.xsum(lvars[n][c] for n,c in s.items())<=len(lvars)-1
      # each node has a unique colour:
      for lv in lvars.values(): M += mip.xsum(lv) == 1
      # for each colour and node cluster, at most one member of that cluster has that colour:
      for r in R:
        for lv in zip(*(lvars[n] for n in r)): M += mip.xsum(lv) <= 1
      # Set initial colours
      for n,c in init: M += lvars[n][c] == 1
      # solve:
      M.verbose = 0
      status = M.optimize()
      if status is mip.OptimizationStatus.OPTIMAL:
        # store and yield solution (colour index for each node):
        sol = {n:argmax([v.x for v in lv]) for n,lv in lvars.items()}
        sols.append(sol)
        yield C,sol
      elif status is mip.OptimizationStatus.INFEASIBLE:
        if sols: return
        else: break # try next number of colours
      else: raise Exception('Internal error',status)

class Multipath:
  r"""
An instance of this class is a multi-path, i.e. a set of edge-disjoint, non contiguous paths with an index of the nodes they visit
  """
  def __init__(self):
    self.paths = paths = []; self.inpath = inpath = defaultdict(set); self.loop = None
    def add(s):
      ends = s[0][0],s[-1][-1]; k = len(paths); paths.append((ends,s))
      for n in (ends[0],*(e[1] for e in s)): inpath[n].add(k)
    self.add = add
  def add_n(self,*nodes:Iterable[int]):
    self.add(list(zip(nodes[:-1],nodes[1:])))
  def __repr__(self):
    x = ' '.join((' '.join(map(str,(f'{k}:[',s[0][0],*(e[1] for e in s),']'))) for k,(_,s) in enumerate(self.paths)))
    return f'{{{x}}}'

  @staticmethod
  def from_oriented_edges(edges:Iterable[Tuple[int,int]])->Multipath:
    r"""
Extracts a :class:`Multipath` object from a set of oriented edges.

:param edges: the list of edges from which to build the nulti-path
    """
    def shuffle(x): x = list(x); random.shuffle(x); return x
    self = Multipath()
    starts = []; links = {}
    adj = defaultdict(lambda: ([],[]))
    for e in edges: adj[e[1]][0].append(e); adj[e[0]][1].append(e)
    for a in adj.values():
      incoming,outgoing = map(shuffle,a)
      links.update(zip(incoming,outgoing))
      starts.extend(outgoing[len(incoming):])
    # creating non-loop paths
    for e in starts:
      s = [e]
      while (e:=links.pop(e,None)) is not None: s.append(e)
      self.add(s)
    # computing standalone loops
    loop_e = set(links); loop_s = []; loops = []; inloop = defaultdict(dict)
    while loop_e:
      e = e0 = loop_e.pop(); k = len(loops); loops.append(k); loop_s.append(e); inloop[e[1]][k] = e
      while (e:=links[e])!=e0: loop_e.remove(e); inloop[e[1]][k] = e
    # merging standalone loops
    for n,d in inloop.items():
      d = dict((loops[k],e) for k,e in d.items())
      if len(d)==1: continue
      (k,*lk),l = zip(*d.items()); e1 = links[l[0]]
      for e,e_ in zip(l[:-1],l[1:]): links[e] = links[e_]
      links[l[-1]] = e1; t = {h:k for h in lk}; loops = [t.get(h,h) for h in loops]
    # integrating standalone loops
    if self.paths: # each loop must be incorporated into a path
      for e0 in (loop_s[k] for k in set(loops)):
        e = e0; s=[]
        while not (l:=self.inpath.get(e[0],())): s.append(e); e = links[e]
        k,*_ = l; ends,s_ = self.paths[k]; i_ = 0 if ends[0]==e[0] else len(s_); s_[i_:i_] = s
        for e_ in s: self.inpath[e_[0]].add(k)
        s = [e]
        while (e:=links[e])!=e0: s.append(e); self.inpath[e[0]].add(k)
        s_[i_:i_] = s
    else: # there should be a single loop and it is returned
      k, = set(loops); e = e0 = loop_s[k]; s = [e0]
      while (e:=links[e]) != e0: s.append(e)
      self.loop = s
    return self

class PolyhedronSpec:
  r"""
Instances of this class are polyhedron specifications. For each :math:`k{\in}0{:}K{-}1`:

* A label :math:`a` with coefficient :math:`z` creates a node at :math:`z\exp{i\frac{2\pi k}{K}}`
* An instruction :math:`(a,b,n)` creates an edge from node :math:`z_a\exp{i\frac{2\pi k}{K}}` to node :math:`z_b\exp{i\frac{2\pi(k{+}n)}{K}}`, where :math:`z_a` (resp. :math:`z_b`) is the coefficient of label :math:`a` (resp. :math:`b`).

:param name: name of the polyhedron
:param K: rotational invariance of angle :math:`\frac{2\pi}{K}`
:param labels: sequence of distinct labels
:param coefs: positions of labels
:param edges: instructions to create edges
:param connect_centre_to: instruction to create edge to centre
  """

  def __init__(self,name:str,K:int,labels:Iterable[str],coefs:Iterable[complex|float|int],edges:Iterable[Tuple[str,str,int]],connect_centre_to:Optional[str]=None):
    self.name,self.K,self.labels,self.coefs,self.edges,self.connect_centre_to = name,K,labels,coefs,edges,connect_centre_to
