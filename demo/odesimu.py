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
from myutil.simpy import SimpySimulation
from ..odesimu import System
Trajectory = namedtuple('Trajectory','periodicity alpha T name display')
Periodicity = Enum('Periodicity','Aperiodic Periodic IncrementalPeriodic')

class Pendulum (System):

  def __init__(self,L,G): self.L,self.G,self.a = L,G,G/L

  def fun(self,t,state): # required
    theta,dtheta = state
    return array((dtheta,-self.a*sin(theta)))

  def jac(self,t,state): # optional
    theta,dtheta = state
    return array(((0,1),(-self.a*cos(theta),0)))

  @staticmethod
  def makestate(theta,dtheta=0.): # required
    return radians((theta, dtheta))

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

  def cartesian(self,state):
    theta,dtheta = state
    return self.L*array((sin(theta),-cos(theta)))

  def trajectory(self,init_y): # precomputes the trajectory
    from scipy.integrate import quad
    theta,dtheta = init_y
    E = .5*square(dtheta)-self.a*cos(theta)
    c = -E/self.a
    if isclose(c,-1):
      periodicity = Periodicity.Aperiodic; name = 'aperiodic'; T = None; α = pi
    else:
      if c<-1: periodicity = Periodicity.IncrementalPeriodic; name = 'incremental period'; α = pi
      else: periodicity = Periodicity.Periodic; name = 'half-period'; α = arccos(c)
      T = pi/sqrt(2) if isclose(α,0.) else quad((lambda θ,c=c: 1/sqrt(cos(θ)-c)),0,α)[0]
      T *= sqrt(2/self.a)
      name = f'{name}: {T:.2f}'
    name = f'CircularArc($R={self.L:.2f}$,$\\alpha={degrees(α):.2f}$) {name}'
    def display(ax):
      from matplotlib.patches import Arc
      ax.set_title(f'Trajectory:{name}',fontsize='x-small')
      ax.scatter(*zip(*map(self.cartesian,((-α,0),(α,0)))),marker='+',c='k')
      ax.add_patch(Arc((0,0),2*self.L,2*self.L,-90,-degrees(α),degrees(α),color='k',ls='dashed'))
    return Trajectory(periodicity,α,T,name,display)

def demo():
  from matplotlib.pyplot import show,close
  syst = Pendulum(L=2.,G=9.81)
  R = SimpySimulation(
    syst.launch(init_y=dict(theta=90.,dtheta=120.),period=10.,cache=(10,.05),max_step=.05),
    play_kw=dict(track=[6.],frame_per_stu=25,fig_kw=dict(figsize=(7,7)),save_count=150),
  )
  def action():
    for a in 'get_size_inches','set_size_inches','savefig': setattr(R.player.board,a,getattr(R.player.main,a)) # very ugly trick because board is a subfigure
    R.player.anim.save(str(RUN.dir/'odesimu.mp4'))
    subprocess.run(['ffmpeg','-loglevel','panic','-y','-i',str(RUN.dir/'odesimu.mp4'),str(RUN.dir/'odesimu.gif')])
    close()
  RUN.play(action)
  show()
