# File:                 polyhedra/util.py
# Creation date:        2022-10-01
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              some utilities on graph
#

from __future__ import annotations
from typing import Any, Union, Callable, Iterable, Generator, Mapping, Tuple, Sequence, Optional, Any
import networkx
from collections import defaultdict
from numpy import random, exp, pi, arange, array, zeros

__all__ = 'Polyhedron', 'Multipath'

class Multipath:
  r"""
An instance of this class is a directed multi-path, i.e. a set of edge-disjoint, non contiguous paths with an index of the nodes they visit.

:param edges: the list of directed edges from which to build the nulti-path
  """
  paths:Sequence[Tuple[Tuple[int,int],Sequence[Tuple[int,int]]]]
  r"""The list of paths (begin-end nodes and list of edges connecting them)"""
  inpath:Mapping[int,set[int]]
  r"""The index, mapping each node to the set of paths (indexed in :attr:`paths`) to which it belongs"""
  def __init__(self,edges:Iterable[Tuple[int,int]]):
    def shuffled(x): x = list(x); random.shuffle(x); return x
    self.paths = paths = []
    self.inpath = inpath = defaultdict(set)
    self.loop = None
    # store starts and links
    starts = []; links = {}
    adj = defaultdict(lambda: ([],[]))
    for e in edges: adj[e[1]][0].append(e); adj[e[0]][1].append(e)
    for a in adj.values():
      incoming,outgoing = map(shuffled,a)
      links.update(zip(incoming,outgoing))
      starts.extend(outgoing[len(incoming):])
    # creating non-loop paths
    for e in starts:
      s = [e]
      while (e:=links.pop(e,None)) is not None: s.append(e)
      ends = s[0][0],s[-1][-1]; k = len(paths); paths.append((ends,s))
      for n in (ends[0],*(e[1] for e in s)): inpath[n].add(k)
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

  def __repr__(self):
    x = ' '.join((' '.join(map(str,(f'{k}:[',s[0][0],*(e[1] for e in s),']'))) for k,(_,s) in enumerate(self.paths)))
    return f'{{{x}}}'

class Polyhedron (networkx.Graph):
  r"""
Instances of this class are polyhedron graphs built from a specification which applies for each :math:`k{\in}0{:}K{-}1` as follows:

* A label :math:`a` with coefficient :math:`z` creates a node :math:`(a,k)` at :math:`z\exp{i\frac{2\pi k}{K}}`
* An instruction :math:`(a,b,n)` creates an edge from node :math:`(a,k)` to node :math:`(b,(k{+}n)\textrm{ mod }K)`

:param name: name of the polyhedron
:param K: rotational invariance of angle :math:`\frac{2\pi}{K}`
:param labels: dictionary of labels with their coefficients
:param edges: instructions to create edges
:param connect_centre_to: instruction to create edge to centre
  """

  def __init__(self,name:str,K:int,labels:Mapping[str,float|complex],edges:Iterable[Tuple[str,str,int]],connect_centre_to:Optional[str]=None,**ka):
    super().__init__(**ka)
    self.graph |= {'name':name,'K':K,'labels':labels,'edges':edges,'connect_centre_to':connect_centre_to}
    Z = exp((2.j*pi/K)*arange(K))
    self.add_nodes_from(((u,k),{'position':array((z.real,z.imag))}) for u,row in zip(labels.keys(),array(list(labels.values()))[:,None]*Z[None,:]) for k,z in enumerate(row))
    self.add_edges_from(((u,k),(v,(k+h)%K)) for k in range(K) for u,v,h in edges)
    if connect_centre_to is not None:
      self.add_node('O',position=zeros(2))
      self.add_edges_from(('O',(connect_centre_to,k)) for k in range(K))
    networkx.freeze(self)

  @staticmethod
  def P4(): return Polyhedron(
    name='tetrahedron',
    K=3,
    labels={'a':1.},
    edges=(('a','a',1),),
    connect_centre_to='a',
  )
  @staticmethod
  def P6(): return Polyhedron(
    name='hexahedron',
    K=4,
    labels={'a':1.,'b':2.},
    edges=(('a','b',0),('a','a',1),('b','b',1)),
  )
  @staticmethod
  def P8(): return Polyhedron(
    name='octahedron',
    K=3,
    labels={'a':1.,'b':-.25},
    edges=(('a','a',1),('b','b',1),('b','a',1),('b','a',-1)),
  )
  @staticmethod
  def P12(): return Polyhedron(
    name='dodecahedron',
    K=5,
    labels={'a':1.,'b':2.,'b_':-3.5,'a_':-5.},
    edges=(('a','b',0),('a_','b_',0),('a','a',1),('a_','a_',1),('b','b_',3),('b_','b',3)),
  )
  @staticmethod
  def P20(): return Polyhedron(
    name='icosahedron',
    K=3,
    labels={'a':1.,'b':4.,'b_':-.25,'a_':-1.},
    edges=(('b_','a_',0),('b_','a',2),('b_','b_',1),('a_','b',2),('a_','a',2),('a','b',0),('a','a_',2),('a','b_',2),('b','a_',2),('b','b',1)),
  )
