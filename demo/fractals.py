# File:                 demo/fractals.py
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Illustration of the fractals subpackage
from make import RUN; RUN(__name__,__file__,2)

#--------------------------------------------------------------------------------------------------

import subprocess
from numpy import square
from ..fractals import MultiZoomFractal, FractalBrowser

mandelbrot = MultiZoomFractal((lambda z,c: square(z)+c),ibounds=((-.779,-.774),(.133,.138)),eoracle=2.)

def demo():
  from matplotlib.pyplot import show,close
  R = FractalBrowser(mandelbrot,fig_kw=dict(figsize=(7,7)),resolution=160000,interval=40,save_count=150)
  def action():
    for a in 'get_size_inches','set_size_inches','savefig': setattr(R.player.board,a,getattr(R.player.main,a)) # very ugly trick because board is a subfigure
    R.player.anim.save(str(RUN.dir/'fractals.mp4'))
    subprocess.run(['ffmpeg','-loglevel','panic','-y','-i',str(RUN.dir/'fractals.mp4'),str(RUN.dir/'fractals.gif')])
    close()
  RUN.play(action)
  show()
