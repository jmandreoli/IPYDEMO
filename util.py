from functools import wraps, partial
from collections import namedtuple
import inspect

class Setup:

  def __init__(self):
    self.repr_ = None
    self.config = {}
    self.visited = []

  def pop(self,f,H,D):
    try: self.visited.remove(f)
    except ValueError: return H,D
    c = self.config.pop(f)
    HH = H+c.helpers; DD = c.defaults.copy(); DD.update(D)
    return HH,DD

  def extend(self,base,*H,**D):
    H = list(tuple(e.strip() for e in h.split(':',1)) for h in H)
    return self.declare(*self.pop(base,H,D))

  def __call__(self,*H,**D):
    return self.declare(list(tuple(e.strip() for e in h.split(':',1)) for h in H),D)

  def declare(self,H,D,Config=namedtuple('Config',('helpers','defaults'))):
    self.repr_ = None
    def tr_(f,F):
      assert inspect.isfunction(f)
      self.config[F] = Config(*self.pop(f,H,D))
      self.visited.append(F)
      return F
    if D:
      def tr(f):
        F = partial(f,**D)
        return tr_(f,wraps(f)(lambda *a,**ka: F(*a,**ka)))
    else: tr = lambda f: tr_(f,f)
    return tr

  def __repr__(self):
    r = self.repr_
    if r is None:
      def h(c,trim=(lambda e: e if len(e)<=10 else '...')):
        D = c.defaults
        for p in c.helpers:
          yield '{:10}{}: {}'.format(p[0],('({:10})'.format(trim(str(D[p[0]]))) if p[0] in D else ''),p[1])
      self.repr_ = r = '\n'.join('**** {} ****\n    {}'.format(f.__qualname__,'\n    '.join(h(self.config[f]))) for f in reversed(self.visited))
    return r

Setup = Setup()
