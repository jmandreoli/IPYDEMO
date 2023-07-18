import mip, networkx
from collections import namedtuple
from numpy import array, argmax, exp, arange, zeros, pi

def colouring(N,R,*init):
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
        else: break
      else: raise Exception('Internal error',status)

PolyhedronSpec = namedtuple('PolyhedronSpec','name K labels coefs edges connect_centre_to',defaults=(None,))
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
def polyhedron(spec,**ka):
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
