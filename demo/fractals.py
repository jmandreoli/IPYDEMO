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

from pathlib import Path; DIR = Path(__file__).parent.resolve()
from functools import partial
from numpy import square
from ..fractals import Fractal
automatic = False

mandelbrot = Fractal((lambda z,c: square(z)+c),ibounds=((-2.5,1.),(-1.,1.)),eradius=2.)

def demo():
  from matplotlib.pyplot import figure, show
  fig = figure(figsize=(8,4))
  a = mandelbrot.launch(fig,maxiter=50)
  if automatic: fig.savefig(str(DIR/'fractals.png'))
  else: show()
