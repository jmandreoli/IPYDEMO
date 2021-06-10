# File:                 demo/odesimu.py
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Illustration of the odesimu subpackage
from make import RUN; RUN(__name__,__file__,2)
#--------------------------------------------------------------------------------------------------

import subprocess
from collections import namedtuple
from enum import Enum
from numpy import array,square,sqrt,cos,sin,arccos,arcsin,degrees,radians,pi,isclose
from ..odesimu import System
Trajectory = namedtuple('Trajectory','periodicity alpha T name display')
Periodicity = Enum('Periodicity','Aperiodic Periodic IncrementalPeriodic')

class Pendulum (System):

  def __init__(self,L,G): self.L,self.G,self.a = L,G,-G/L

  def fun(self,t,state): # required
    theta,dtheta = state
    return array((dtheta,self.a*sin(theta)))

  def jac(self,t,state): # optional
    theta,dtheta = state
    return array(((0,1),(self.a*cos(theta),0)))

  @staticmethod
  def makestate(theta,dtheta=0.): return radians((theta,dtheta)) # required

  def displayer(self,env,ax,refsize=None): # required
    trajectory = self.trajectory(env.init_y)
    ax.set_title(f'trajectory:{trajectory.name}',fontsize='x-small')
    L = 1.05*self.L
    ax.set(xlim=(-L,L),ylim=(-L,L))
    ax.scatter((0.,),(0.,),c='k',marker='o',s=refsize)
    trajectory.display(ax)
    a_pole, = ax.plot((),(),'k')
    a_bob = ax.scatter((),(),s=refsize,marker='o',c='r')
    a_tail, = ax.plot((),(),'y')
    def disp():
      x,y = self.cartesian(env.state)
      a_pole.set_data((0,x),(0,y))
      a_bob.set_offsets(((x,y),))
      a_tail.set_data(*self.cartesian(env.cached_states))
    return disp

  def trajectory(self,ini):
    from scipy.integrate import quad
    theta,dtheta = ini
    c = .5*square(dtheta)/self.a+cos(theta)
    if isclose(c,-1):
      periodicity = Periodicity.Aperiodic; name = 'aperiodic'; T = None; alpha = pi
    else:
      if c<-1: periodicity = Periodicity.IncrementalPeriodic; name = 'incremental period'; alpha = pi
      else: periodicity = Periodicity.Periodic; name = 'half-period'; alpha = arccos(c)
      T = pi/sqrt(2) if isclose(alpha,0.) else quad((lambda theta,c=c: 1/sqrt(cos(theta)-c)),0,alpha)[0]
      T *= sqrt(2/self.a)
      name = f'{name}: {T:.2f}'
    name = f'CircularArc($R$={self.L:.2f},$\\alpha$={degrees(alpha):.2f}) {name}'
    def display(ax):
      from matplotlib.patches import Arc
      ax.scatter(*zip(*map(self.cartesian,((-alpha,0),(alpha,0)))),marker='+',c='k')
      ax.add_patch(Arc((0,0),2*self.L,2*self.L,-90,-degrees(alpha),degrees(alpha),color='k',ls='dashed'))
    return Trajectory(periodicity,alpha,T,name,display)

  def cartesian(self,state):
    theta,dtheta = state
    return self.L*array((sin(theta),-cos(theta)))

def demo():## TO BE REVISED
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
