# File:                 polyhedra/core.py
# Creation date:        2022-10-01
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              some graph algorithms, esp. for polyhedra
#

from __future__ import annotations
import logging; logger = logging.getLogger(__name__)
from typing import Any, Union, Callable, Iterable, Generator, Mapping, Tuple, List, Optional, Any
from collections import defaultdict
from itertools import islice
from numpy import linalg, array, hstack, prod, sign, exp, arange, zeros, pi
from .util import colouring, Multipath, PolyhedronSpec
import networkx, mip

__all__ = 'draw', 'min_edge_colouring', 'min_path_cover', 'min_thread_colouring', 'polyhedron', 'RegularPolyhedra', 'Multipath'

def draw(G:networkx.Graph,E_COLOURS:Optional[Mapping[int,str]]=None,N_COLOURS:Optional[Mapping[int,str]]=None,TITLE:str='{name}',**ka):
  r"""
Draws multiple views of a graph. The views differ only by the colouring of nodes and edges. Assumptions:

* *G* has a graph attribute `views`, which is a dict mapping each view name to a title
* Each node of *G* has a node attribute `position` as an array (in 2D)
* Each node and each edge of *G* may have a node or edge attribute `colour`, which is a dict mapping each of a set of view names to a colour index
* *G* may have graph attribute `e_colours` (resp. `n_colours`), which is a dict mapping edge (resp. node) colour indices to matplotlib colour names

:param G: the graph to draw
:param E_COLOURS: dict mapping edge colour indices to matplotlib colour names, overriding the items in attribute `e_colours` of *G*
:param N_COLOURS: dict mapping node colour indices to matplotlib colour names, overriding the items in attribute `n_colours` of *G*
:param TITLE: string format for the title of the overall figure (the format variables are the graph attribute names)
  """
  from matplotlib.pyplot import subplots
  e_colours:Mapping[int,str] = G.graph.get('e_colours',{}) | ({} if E_COLOURS is None else dict(E_COLOURS))
  n_colours:Mapping[int,str] = G.graph.get('n_colours',{}) | ({} if N_COLOURS is None else dict(N_COLOURS))
  views = G.graph.get('views',{None:f'Graph[Vertices:{G.order()}, Edges:{G.size()}, Faces:{G.size()-G.order()+2}]'})
  rows,cols = map((lambda n: n+1),divmod(len(views)-1,4))
  if rows>1: cols = 4
  fig,axes = subplots(rows,cols,squeeze=False,subplot_kw=dict(aspect='equal',xticks=(),yticks=(),frame_on=False),figsize=(4*cols,4*rows))
  for (view,title),ax in zip(views.items(),(ax for axes_ in axes for ax in axes_)):
    networkx.draw(G,
                  pos=dict([(n,r['position']) for n,r in G.nodes.items()]),
                  node_color=[n_colours.get(r.get('colour',{}).get(view),'black') for r in G.nodes.values()],
                  edge_color=[e_colours.get(r.get('colour',{}).get(view),'gray') for r in G.edges.values()],
                  ax=ax,
                  **(dict(with_labels=False,node_size=20,width=3)|ka))
    ax.set_title(title,size='x-small')
  fig.suptitle(G.graph.get('title',TITLE).format(**G.graph),size='small')

def min_edge_colouring(G:networkx.Graph,*init:Iterable[Tuple[Any,int]],nsol:int=4)->networkx.Graph:
  r"""
Sets the node and edge colours of an undirected graph, so that no two contiguous edges have the same colour.

:param G: an undirected graph
:param init: a list of (edge,colour) pairs which is imposed in each solution
:param nsol: max number of solutions generated
  """
  def orientation(mat): mat = array([u for u in mat if u is not None]); return prod([linalg.det(mat[[0,i,i+1]]) for i in range(1,len(mat)-1)])
  assert not networkx.is_directed(G)
  # list edges accounting for non directedness
  edges = {e_:e for e in G.edges for e_ in (e,e[::-1])}
  Cs,sols = zip(*islice(colouring(G.edges,[[edges[n,m] for m in l] for n,l in G.adj.items()],*((edges[tuple(e)],c) for *e,c in init)),nsol))
  C, = set(Cs)
  for e,r in G.edges.items(): r['colour'] = {i:s[e] for i,s in enumerate(sols)}
  G.graph['e_colours'] = dict(enumerate('rgbcmy'))
  # adjust node colouring
  orient = [{n:[None for _ in range(C)] for n in G.nodes} for _ in sols]
  for e in G.edges:
    u = G.nodes[e[1]]['position']-G.nodes[e[0]]['position']; u /= linalg.norm(u)
    for n,v in zip(e,(u,-u)):
      for mat,sol in zip(orient,sols): mat[n][sol[e]] = hstack((v,1.))
  for n,r in G.nodes.items():
    r['colour'] = {i:int(sign(orientation(mat[n]))) for i,mat in enumerate(orient)}
  G.graph['n_colours'] = {1:'k',-1:'w'}
  G.graph['views'] = {i:f'{C}-colour generated sample [{i+1}]' for i in range(len(sols))}
  G.graph['title'] = 'min-edge-colouring[{name}]'
  return G

def min_path_cover(G:networkx.Graph)->Generator[Multipath]:
  r"""
Computes the minimum number of edge-disjoint paths needed to cover all the edges of an undirected graph.

A solution is a :class:`Multipath` object.

This is solved by MILP. If :math:`v` is a vertice and :math:`e` an edge, let :math:`\gamma(v,e)=1` if :math:`e` is adjacent to :math:`v` and :math:`0` otherwise.

* Variables:

  * one integer variable :math:`x_e` for each edge :math:`e`, specifying its orientation in the multi-path: :math:`+1` if it is the edge's orientation and :math:`-1` otherwise
  * one integer variable :math:`x_v` for each vertex :math:`v`, representing an upper bound of the degree flow (absolute value of out-degree minus in-degree in the multi-path)

* By definition, any vertex :math:`v` satisfies :math:`|\sum_e\gamma(v,e)x_e|\leq x_v`
* The objective is to minimize :math:`\sum_vx_v`, which is twice the number of paths in the multi-path

:param G: an undirected graph
:return: a pair of the number of covering paths, and a random solution
  """
  assert not networkx.is_directed(G)
  M = mip.Model(); sols = []; O = None
  while True:
    M.clear(); e_vars = {}; n_vars = defaultdict(list); objc = []
    # create an integer variable in {-1,+1} for each edge:
    for e in G.edges:
      v = M.add_var(var_type=mip.BINARY); e_vars[e] = v2 = M.add_var(var_type=mip.INTEGER,lb=-1,ub=1)
      M += v2 == 2*v-1
      for n,t in zip(e,(v2,-v2)): n_vars[n].append(t)
    # force current solution to be distinct from all previous ones:
    for sol in sols: M += mip.xsum(sol[e]*v for e,v in e_vars.items())<=len(e_vars)-1
    # create an integer variable for each node:
    for n,l in n_vars.items():
      v = M.add_var(var_type=mip.INTEGER,lb=0,ub=len(l))
      # constrain it to be a bound on the degree flow
      objc.append(v); t = mip.xsum(l); M += t<=v; M += -t<=v
    objc = mip.xsum(objc)
    # objective: sum of bounds on the degree flow at each vertice
    if O is None: M.objective = objc
    else: M += objc <= O
    # solve
    M.verbose = False
    status = M.optimize()
    if status is mip.OptimizationStatus.OPTIMAL:
      sol = {e:int(round(v.x)) for e,v in e_vars.items()}; sols.append(sol)
      res = Multipath.from_oriented_edges([e[::o] for e,o in sol.items()])
      O_ = int(round(objc.x))
      if O is None:
        if O_==0: assert res.loop is not None; yield res; return # the whole graph is a single loop
        O = O_; T,rem = divmod(O,2); assert rem==0 and len(res.paths) == T
      else: assert O_==O
      yield res
    elif status is mip.OptimizationStatus.INFEASIBLE: return
    else: raise Exception('Internal error',status)

def min_thread_colouring(G:networkx.Graph,manual:Iterable[Multipath]=(),nsol:int=4)->networkx.Graph:
  r"""
Colours the paths of an undirected graph, so that no two intersecting paths have the same colour.

:param G: an undirected graph
:param manual: a sequence
  """
  def gen(r):
    if r.loop is None:
      _,col = next(colouring(range(len(r.paths)),r.inpath.values()))
      yield from ((e,c) for (c,(_,s)) in zip(col,r.paths) for e in s)
    else: # res is a single loop
      yield from ((e,0) for e in r.loop)
  sols = dict(islice(((gen(r),f'{len(r.paths)}-thread {mode} sample [{i+1}]') for mode,src in (('manual',manual),('generated',min_path_cover(G))) for i,r in enumerate(src)),nsol))
  D = {(sol,e_):c for sol in sols for e,c in sol for e_ in (e,e[::-1])}
  for e in G.edges: G.edges[e]['colour'] = {sol:c for sol in sols if (c:=D.get((sol,e))) is not None}
  G.graph['views'] = sols
  G.graph['e_colours'] = dict(enumerate('rgbcmy'))
  G.graph['title'] = 'min-threading[{name}]'
  return G

RegularPolyhedra = {
  4:PolyhedronSpec(
    name='tetrahedron',
    K=3,
    labels=('a',),
    coefs=1.,
    edges=(('a','a',1),),
    connect_centre_to='a',
  ),
  6:PolyhedronSpec(
    name='hexahedron',
    K=4,
    labels=('a','b'),
    coefs=array((1.,2.))[:,None],
    edges=(('a','b',0),('a','a',1),('b','b',1)),
  ),
  8:PolyhedronSpec(
    name='octahedron',
    K=3,
    labels=('a','b'),
    coefs=array((1.,-.25))[:,None],
    edges=(('a','a',1),('b','b',1),('b','a',1),('b','a',-1)),
  ),
  12:PolyhedronSpec(
    name='dodecahedron',
    K=5,
    labels=('a','b','b_','a_'),
    coefs=array((1.,2.,-3.5,-5.))[:,None],
    edges=(('a','b',0),('a_','b_',0),('a','a',1),('a_','a_',1),('b','b_',3),('b_','b',3)),
  ),
  20:PolyhedronSpec(
    name='icosahedron',
    K=3,
    labels=('a','b','b_','a_'),
    coefs=array((1.,4.,-.25,-1.))[:,None],
    edges=(('b_','a_',0),('b_','a',2),('b_','b_',1),('a_','b',2),('a_','a',2),('a','b',0),('a','a_',2),('a','b_',2),('b','a_',2),('b','b',1)),
  ),
}
def polyhedron(spec:PolyhedronSpec|int,**ka):
  if isinstance(spec,int): spec = RegularPolyhedra[spec]
  G = networkx.Graph(name=spec.name,**ka)
  Z = exp((2.j*pi/spec.K)*arange(spec.K))
  G.add_nodes_from(((n,k),{'position':array((z.real,z.imag))}) for n,row in zip(spec.labels,array(spec.coefs)*Z[None,:]) for k,z in enumerate(row))
  G.add_edges_from(((u,k),(v,(k+h)%spec.K)) for k in range(spec.K) for u,v,h in spec.edges)
  if spec.connect_centre_to is not None:
    G.add_node('O',position=zeros(2))
    G.add_edges_from(('O',(spec.connect_centre_to,k)) for k in range(spec.K))
  networkx.freeze(G)
  return G
