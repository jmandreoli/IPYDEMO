# File:                 demo/fractals.py
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Illustration of the fractals subpackage
from make import RUN; RUN(__name__,__file__) # trick for documentation

#--------------------------------------------------------------------------------------------------

from numpy import square
from IPYDEMO.fractals import MultiZoomFractal, FractalBrowser

mandelbrot = MultiZoomFractal((lambda z,c: square(z)+c),ibounds=((-.779,-.774),(.133,.138)),eoracle=2.)

R = FractalBrowser(mandelbrot,fig_kw={'figsize':(7,7)},resolution=160000,interval=40,save_count=150)
RUN.save(R.player)
