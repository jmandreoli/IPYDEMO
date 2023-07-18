# File:                 polyhedra/core.py
# Creation date:        2022-10-01
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              some graph algorithms, esp. for polyhedra
#

from __future__ import annotations
import logging; logger = logging.getLogger(__name__)
from typing import Any, Union, Callable, Iterable, Mapping, Tuple
from collections import defaultdict
from itertools import islice
from numpy import linalg, random, array, hstack, prod, sign
import networkx, mip

__all__ = 'draw', 'min_edge_colouring', 'min_path_cover', 'min_thread_colouring'

def draw(G:networkx.Graph,E_COLOURS:Mapping[int,str]=None,N_COLOURS=Mapping[int,str],TITLE:str='{name}',**ka):
  from matplotlib.pyplot import subplots
  E_COLOURS:Mapping[int,str] = G.graph.get('e_colours',{}) | ({} if E_COLOURS is None else dict(E_COLOURS))
  N_COLOURS:Mapping[int,str] = G.graph.get('n_colours',{}) | ({} if N_COLOURS is None else dict(N_COLOURS))
  views = G.graph.get('views',{None:'Graph[Vertices:{v}, Edges:{e}, Faces:{f}]'.format(v=G.order(),e=G.size(),f=G.size()-G.order()+2)})
  rows,cols = map((lambda n: n+1),divmod(len(views)-1,4))
  if rows>1: cols = 4
  fig,axes = subplots(rows,cols,squeeze=False,subplot_kw=dict(aspect='equal',xticks=(),yticks=(),frame_on=False),figsize=(4*cols,4*rows))
  for (view,title),ax in zip(views.items(),(ax for axes_ in axes for ax in axes_)):
    networkx.draw(G,
                  pos=dict([(n,r['position']) for n,r in G.nodes.items()]),
                  node_color=[N_COLOURS.get(r.get('colour',{}).get(view),'black') for r in G.nodes.values()],
                  edge_color=[E_COLOURS.get(r.get('colour',{}).get(view),'gray') for r in G.edges.values()],
                  ax=ax,
                  **(dict(with_labels=False,node_size=20,width=3)|ka))
    ax.set_title(title,size='x-small')
  fig.suptitle(G.graph.get('title',TITLE).format(**G.graph),size='small')

def min_edge_colouring(G,*init,nsol=4):
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

class Multipath:
  # An instance of this class is a multi-path, i.e. a set of edge-disjoint paths with an index of the nodes they visit
  def __init__(self):
    self.paths = paths = []; self.inpath = inpath = defaultdict(set)
    def add(s):
      ends = s[0][0],s[-1][-1]; k = len(paths); paths.append((ends,s))
      for n in (ends[0],*(e[1] for e in s)): inpath[n].add(k)
    self.add = add
  def add_n(self,*nodes): self.add(list(zip(nodes[:-1],nodes[1:])))
  def __repr__(self):
    x = ' '.join((' '.join(map(str,(f'{k}:[',s[0][0],*(e[1] for e in s),']'))) for k,(_,s) in enumerate(self.paths)))
    return f'{{{x}}}'

def min_path_cover(G):
  def make(sol):
    # build a random multi-path from milp solution
    def shuffle(x): x = list(x); random.shuffle(x); return x
    sol_ = {e[::o]:o*x for e,x in sol.items() for o in (1,-1)}
    mp = Multipath(); starts = []; links = {}
    for n,l in G.adj.items():
      l_ = [((n,m),sol_[n,m]) for m in l]
      l1,l2 = map(shuffle,([e[::o] for e,o in l_ if o==o_] for o_ in (-1,1)))
      links.update(zip(l1,l2)); starts.extend(l2[len(l1):])
    # creating non-loop paths
    for e in starts:
      s = [e]
      while (e:=links.pop(e,None)) is not None: s.append(e)
      mp.add(s)
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
    if mp.paths: # each loop must be incorporated into a path
      for e0 in (loop_s[k] for k in set(loops)):
        e = e0; s=[]
        while not (l:=mp.inpath.get(e[0],())): s.append(e); e = links[e]
        k,*_ = l; ends,s_ = mp.paths[k]; i_ = 0 if ends[0]==e[0] else len(s_); s_[i_:i_] = s
        for e_ in s: mp.inpath[e_[0]].add(k)
        s = [e]
        while (e:=links[e])!=e0: s.append(e); mp.inpath[e[0]].add(k)
        s_[i_:i_] = s
      return mp
    else: # there should be a single loop and it is returned
      k, = set(loops); e = e0 = loop_s[k]; s = [e0]
      while (e:=links[e]) != e0: s.append(e)
      return s
  assert not networkx.is_directed(G)
  M = mip.Model(); sols = []; O = T = None
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
      sol = {e:int(round(v.x)) for e,v in e_vars.items()}; sols.append(sol); res = make(sol)
      O_ = int(round(objc.x))
      if O is None:
        if O_==0: assert not isinstance(res,Multipath); yield 0,res; break # the whole graph is a single loop
        O = O_; T,rem = divmod(O,2); assert rem==0
      else: assert O_==O
      yield T,res
    elif status is mip.OptimizationStatus.INFEASIBLE:
      if sols: return
      else: break
    else: raise Exception('Internal error',status)

def min_thread_colouring(G,manual=(),nsol=4):
  def gen(T,r):
    if isinstance(r,Multipath):
      _,col = next(colouring(range(T),r.inpath.values()))
      yield from ((e,c) for k,(_,s) in enumerate(r.paths) for c in {col[k]} for e in s)
    else: # res is a single loop
      assert T==0
      yield from ((e,0) for e in r)
  sols = dict(islice(((gen(T,r),f'{T}-thread {mode} sample [{i+1}]') for mode,src in (('manual',manual),('generated',min_path_cover(G))) for i,(T,r) in enumerate(src)),nsol))
  D = {(sol,e_):c for sol in sols for e,c in sol for e_ in (e,e[::-1])}
  for e in G.edges: G.edges[e]['colour'] = {sol:c for sol in sols if (c:=D.get((sol,e))) is not None}
  G.graph['views'] = sols
  G.graph['e_colours'] = dict(enumerate('rgbcmy'))
  G.graph['title'] = 'min-threading[{name}]'
  return G
