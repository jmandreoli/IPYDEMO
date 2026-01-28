# File:                 demo/polyhedra.py
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Illustration of the polyhedra subpackage

from IPYDEMO.polyhedra import draw, min_edge_colouring, min_thread_colouring, Polyhedron


def P12(): return Polyhedron(
  # given for illustration: all the Platonic polyhedra are predefined in class Polyhedron
  name='dodecahedron',
  K=5,
  labels={'a':1.,'b':2.,'b_':-3.5,'a_':-5.},
  edges=(('a','b',0),('a_','b_',0),('a','a',1),('a_','a_',1),('b','b_',3),('b_','b',3)),
)

draw(P12()).savefig(RUN.path('.png'))

G = {
  'ec':(min_edge_colouring(P12(),*((('a',k),('a',k+1),k%2) for k in range(4))),{'E_COLOURS':enumerate('cmy')}),
  'tc':(min_thread_colouring(P12(),nsol=2),{}),
}
for k,(g,a) in G.items(): draw(g,**a).savefig(RUN.path('.png',k))
