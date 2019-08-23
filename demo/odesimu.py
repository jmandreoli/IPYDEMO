# File:                 demo/odesimu.py
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Illustration of the odesimu subpackage
from make import RUN; RUN(__name__,__file__,2)
#--------------------------------------------------------------------------------------------------

import subprocess
from functools import partial
from numpy import array,square,sqrt,cos,sin,arccos,arcsin,degrees,radians,pi,nan
from ..odesimu import System

class Pendulum (System):

  shadowshape = (2,)

  def __init__(self,L,G): self.L,self.G,self.a = L,G,-G/L

  def main(self,t,state): # required
    theta,dtheta = state
    return array((dtheta,self.a*sin(theta)))

  def jacobian(self,t,state): # optional
    theta,dtheta = state
    return array(((0,1),(self.a*cos(theta),0)))

  def fordisplay(self,state): # required
    theta,dtheta = state
    pos = self.L*array((sin(theta),-cos(theta)))
    return pos, pos

  def display(self,ax,refsize=None,ini=None,**ka): # required
    from matplotlib.patches import Arc
    L = 1.05*self.L; ax.set_xlim(-L,L); ax.set_ylim(-L,L)
    ax.scatter((0.,),(0.,),c='k',marker='o',s=refsize)
    T, alpha = self.trajectory(ini)
    ax.scatter((-self.L*sin(alpha),self.L*sin(alpha)),(-self.L*cos(alpha),-self.L*cos(alpha)),marker='o',c='none')
    alphadeg = degrees(alpha)
    ax.add_patch(Arc((0.,0.),2*self.L,2*self.L,theta1=-alphadeg-90,theta2=alphadeg-90,ls='--',ec='r'))
    ax.set_title(r'Pendulum[length:{:.2f}$m$ gravity:{:.2f}$ms^{{-2}}$ period:{:.2f}$s$]'.format(self.L,self.G,T),fontsize='small')
    #
    rod_a, = ax.plot((),(),'k')
    bob_a = ax.scatter((),(),s=refsize,marker='o',c='r')
    shadow_a, = ax.plot((),(),'g',lw=3)
    #
    def disp(t,live,tail):
      x,y = live
      rod_a.set_data((0,x),(0,y))
      bob_a.set_offsets(((x,y),))
      shadow_a.set_data(tail[:,0],tail[:,1])
    #
    return super().display(ax,disp,ini=ini,**ka)

  def trajectory(self,ini):
    from scipy.integrate import quad
    theta,dtheta = ini
    c = .5*square(dtheta)/self.a+cos(theta)
    k,alpha = (1,pi) if c<-1 else (nan,pi) if c==-1 else (2,arccos(c)) if c<1 else (nan,0)
    T = pi/sqrt(2) if alpha<.1 else quad((lambda theta,c=c: 1/sqrt(cos(theta)-c)),0,alpha)[0]
    T *= k*sqrt(-2/self.a)
    return T,alpha

  @staticmethod
  def makestate(theta,dtheta=0.): return radians((theta,dtheta))

def demo():
  from matplotlib.pyplot import figure,show,close
  syst = Pendulum(L=1.,G=9.81)
  fig = figure(figsize=(9,10))
  anim = syst.launch(fig,ini=syst.makestate(theta=90.,dtheta=240.),taild=.5,refsize=50.,maxtime=3.)
  def action():
    anim.save(str(RUN.dir/'odesimu.mp4'))
    subprocess.run(['ffmpeg','-loglevel','panic','-y','-i',str(RUN.dir/'odesimu.mp4'),str(RUN.dir/'odesimu.gif')])
    close()
  RUN.play(action)
  show()
