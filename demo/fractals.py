# File:                 demo/odesimu.py
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Illustration of the odesimu subpackage
from make import RUN; RUN(__name__,__file__,2)

#--------------------------------------------------------------------------------------------------

import subprocess
from functools import partial
from numpy import square
from ..fractals import Fractal

mandelbrot = Fractal((lambda z,c: square(z)+c),ibounds=((-.779,-.774),(.133,.138)),eradius=2.)

def demo():
  from matplotlib.pyplot import figure, show, close
  fig = figure(figsize=(8,4))
  anim = mandelbrot.launch(fig,maxiter=100,interval=40)
  def action():
    anim.save(str(RUN.dir/'fractals.mp4'))
    subprocess.run(['ffmpeg','-loglevel','panic','-y','-i',str(RUN.dir/'fractals.mp4'),str(RUN.dir/'fractals.gif')])
    close()
  RUN.play(action)
  show()
