from functools import wraps, partial
from collections import namedtuple
import inspect, re

class Setup:

  def __init__(self):
    self.repr_ = self.html_ = None
    self.config = {}
    self.visited = []

  def extend(self,base,*H,**D):
    return self.declare(*self.pop(base,list(map(self.parse,H)),D))

  def __call__(self,*H,**D):
    return self.declare(list(map(self.parse,H)),D)

  def pop(self,f,H,D):
    try: self.visited.remove(f)
    except ValueError: return H,D
    c = self.config.pop(f)
    HH = H+c.helpers; DD = c.defaults.copy(); DD.update(D)
    return HH,DD

  def declare(self,H,D,Config=namedtuple('Config',('helpers','defaults'))):
    self.repr_ = self.html_ = None
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

  def parse(self,h,pat=re.compile(r'(?P<argn>(?:\w|,)+?)\s*:\s+(?P<help>[^[]+)(?:\s+\[(?P<unit>(?:\w+(?:\^-?[0-9]+)?)(?:\.\w+(?:\^-?[0-9]+)?)*)\])?'),upat=re.compile(r'(?P<base>[^\^]+)(?:\^(?P<expn>.+))?'),Helper=namedtuple('Helper',('argn','help','unit'))):
    def unit(x):
      g = upat.fullmatch(x).groups()
      return g[0],(1 if g[1] is None else int(g[1]))
    g = pat.fullmatch(h.strip()).groups()
    return Helper(g[0],g[1],(None if g[2] is None else tuple(unit(x) for x in g[2].split('.'))))

  def _repr_html_(self):
    from lxml.builder import E
    from lxml.etree import tostring
    def un(u):
      sep = None
      for base,expn in u:
        if sep is not None: yield sep
        yield E.SPAN(base)
        if expn!=1: yield E.SUP(str(expn))
        sep = ' '
    def row():
      for f in reversed(self.visited):
        yield E.TR(E.TD(pname(f),colspan='4',style='background-color: gray; color: white; font-weight: bold;'))
        c = self.config[f]
        for h in c.helpers:
          yield E.TR(E.TH(h.argn),E.TD((repr(c.defaults[h.argn]) if h.argn in c.defaults else ''),style='max-width:2cm; white-space: nowrap; overflow: hidden'),E.TD(h.help),*(() if h.unit is None else (E.TD(*un(h.unit)),)))
    return tostring(E.TABLE(E.TBODY(*row())),encoding='unicode')

  def __repr__(self):
    r = self.repr_
    if r is None:
      def row(c,trim=(lambda x: repr(x)[:10])):
        for h in c.helpers:
          dv = '({:10})'.format(trim(c.defaults[h.argn])) if h.argn in c.defaults else ''
          un = '' if h.unit is None else ' [{}]'.format('.'.join('{}{}'.format(x[0],('^{}'.format(x[1]) if x[1]!=1 else '')) for x in h.unit))
          yield '{:10}{}: {}{}'.format(h.argn,dv,h.help,un)
      self.repr_ = r = '\n'.join('**** {} ****\n    {}'.format(pname(f),'\n    '.join(row(self.config[f]))) for f in reversed(self.visited))
    return r

Setup = Setup()

def pname(f):
  return '{}{}'.format(f.__qualname__,inspect.signature(f))
