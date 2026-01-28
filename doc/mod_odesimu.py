# File:                 demo/odesimu.py
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Illustration of the odesimu subpackage

from numpy import array,square,sqrt,cos,sin,arccos,arcsin,degrees,radians,pi,isclose
from IPYDEMO.odesimu import ODESystem
from collections import namedtuple
from enum import Enum
Periodicity = Enum('Periodicity','Aperiodic Periodic IncrementalPeriodic')
Analytics = namedtuple('Analytics','E alpha periodicity T name displayer')

class Pendulum (ODESystem):

  def __init__(self,L,G):
    a = G/L; self.L,self.G,self.a = L,G,a
    def fun(t,state): # required
      theta,dtheta = state
      return array((dtheta,-a*sin(theta)))
    self.fun = fun
    def jac(t,state): # optional
      theta,dtheta = state
      return array(((0,1),(-a*cos(theta),0)))
    self.jac = jac
    super().__init__()

  @staticmethod
  def makestate(theta,dtheta=0.): # required
    return radians((theta, dtheta))

  def displayer(self,trajectory,ax,refsize=None): # required
    Q = self.analytics(trajectory.init_y)
    ax.set_title(Q.name,fontsize='x-small')
    L = 1.05*self.L
    ax.set(xlim=(-L,L),ylim=(-L,L))
    ax.scatter((0.,),(0.,),c='k',marker='o',s=refsize)
    Q.displayer(ax)
    a_pole, = ax.plot((),(),'k')
    a_bob = ax.scatter((),(),s=refsize,marker='o',c='r')
    a_tail, = ax.plot((),(),'y')
    def disp(t):
      x,y = self.cartesian(trajectory.state(t))
      a_pole.set_data((0,x),(0,y))
      a_bob.set_offsets(((x,y),))
      a_tail.set_data(*self.cartesian(trajectory.cached(t)))
    return disp

  def cartesian(self,state):
    theta,dtheta = state
    return self.L*array((sin(theta),-cos(theta)))

  trajectory_defaults = {'period':10.,'cache_spec':(10,.05),'max_step':.05}

  def analytics(self,ini): # optional
    from scipy.integrate import quad
    θ,θʹ = ini
    E = .5*square(θʹ)-self.a*cos(θ)
    c = -E/self.a
    if isclose(c,-1):
      α,periodicity,T,fmt = pi,Periodicity.Aperiodic,None,'aperiodic'
    else:
      α,periodicity,fmt = (pi,Periodicity.IncrementalPeriodic,'incremental period: {:.2f}') if c<-1 else (arccos(c),Periodicity.Periodic,'half-period: {:.2f}')
      T = pi/sqrt(2) if isclose(α,0.) else quad((lambda θ,c=c: 1/sqrt(cos(θ)-c)),0,α)[0]
      T *= sqrt(2/self.a)
    name = f'CircularArc($R={self.L:.2f},\\alpha={degrees(α):.2f}^\\circ$) {fmt.format(T)}'
    def displayer(ax):
      from matplotlib.patches import Arc
      ax.set_title(f'Motion:{name}',fontsize='x-small')
      ax.scatter(*zip(*map(self.cartesian,((-α,0),(α,0)))),marker='+',c='k')
      ax.add_patch(Arc((0,0),2*self.L,2*self.L,angle=-90,theta1=-degrees(α),theta2=degrees(α),color='k',ls='dashed'))
    return Analytics(E,α,periodicity,T,name,displayer)

syst = Pendulum(L=2.,G=9.81)
sim = syst.simulation(init_y={'theta':90.,'dtheta':120.},period=20.)
RUN.record(sim.play(track_spec=[6.],frame_per_stu=25,fig_kw={'figsize':(7,7)},save_count=150))
