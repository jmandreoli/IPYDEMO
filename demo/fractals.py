# File:                 demo/odesimu.py
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Illustration of the odesimu subpackage

if __name__=='__main__':
  import sys
  from ipyshow.demo.fractals import demo
  demo()
  sys.exit(0)

#--------------------------------------------------------------------------------------------------
from functools import partial
from numpy import square
from ..fractals.fractal import Fractal

@partial(Fractal,ibounds=((-2.5,1.),(-1.,1.)),eradius=2.)
def mandelbrot(c): # note: must work as a u-func
  z = c.copy()
  while True:
    yield z
    square(z,out=z)
    z += c

def demo():
  from matplotlib.pyplot import show
  a = mandelbrot.launch(fig=dict(figsize=(8,4)),maxiter=50)
  show()
