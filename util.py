from functools import wraps, partial
from collections import namedtuple, OrderedDict
import inspect, re

class Setup:

  def __init__(self):
    self.reprs_ = None
    self.config = OrderedDict()
    self.unprocessed = []

  def __call__(self,*H,**D): return self.declare(H,D,False)
  def abstract(self,*H,**D): return self.declare(H,D,True)
  def declare(self,H,D,abstract):
    H = OrderedDict(map(self.parse,H))
    self.reprs_ = None
    def tr(f):
      assert inspect.isfunction(f)
      F = (lambda F: wraps(f)(lambda *a,**ka: F(*a,**ka)))(partial(f,**D)) if D else f
      F.setup = H,D,abstract
      self.unprocessed.append(F)
      return F
    return tr

  @staticmethod
  def parse(h,pat=re.compile(r'(?P<argn>(?:\w|,)+?)\s*:\s+(?P<help>[^[]+)(?:\s+\[(?P<unit>(?:\w+(?:\^-?[0-9]+)?)(?:\.\w+(?:\^-?[0-9]+)?)*)\])?'),upat=re.compile(r'(?P<base>[^\^]+)(?:\^(?P<expn>.+))?')):
    def unit(x):
      g = upat.fullmatch(x).groups()
      return g[0],(1 if g[1] is None else int(g[1]))
    g = pat.fullmatch(h.strip()).groups()
    return g[0],(g[1],(None if g[2] is None else tuple(unit(x) for x in g[2].split('.'))))

  def _repr_html_(self): return self.reprs['html']
  def __repr__(self): return self.reprs['txt']

  @property
  def reprs(self):
    r = self.reprs_
    if r is None: self.reprs_ = r = self.genreprs()
    return r

  def genreprs(self,Config=namedtuple('Config',('helpers','defaults'))):
    self.config.clear()
    for f in self.unprocessed:
      H,D,abstract = f.setup
      if abstract: continue
      HH,DD = H.copy(),D.copy()
      for ff in reversed(tuple(mro(f))):
        if hasattr(ff,'setup'): H,D,a = ff.setup; HH.update(H); DD.update(D)
      self.config[f] = Config(HH,DD)
    self.unprocessed = []
    return dict(txt=self.as_txt(),html=self.as_html())

  def as_txt(self):
    def rows(trim):
      for f,c in reversed(self.config.items()):
        yield '**** {} ****'.format(pname(f))
        for argn,(txt,unit) in c.helpers.items():
          dv = '({:10})'.format(trim(c.defaults[argn])) if argn in c.defaults else ''
          unit = '' if unit is None else ' [{}]'.format('.'.join('{}{}'.format(x[0],('^{}'.format(x[1]) if x[1]!=1 else '')) for x in unit))
          yield '    {:10}{}: {}{}'.format(argn,dv,txt,unit)
    return '\n'.join(rows((lambda x: repr(x)[:10])))

  def as_html(self):
    from lxml.builder import E
    from lxml.etree import tostring
    def uncomp(u):
      sep = None
      for base,expn in u:
        if sep is not None: yield sep
        yield E.SPAN(base)
        if expn!=1: yield E.SUP(str(expn))
        sep = ' '
    def rows():
      for f,c in reversed(self.config.items()):
        yield E.TR(E.TD(pname(f),colspan='4',style='background-color: gray; color: white; font-weight: bold;'))
        for argn,(txt,unit) in c.helpers.items():
          yield E.TR(E.TH(argn),E.TD((repr(c.defaults[argn]) if argn in c.defaults else ''),style='max-width:2cm; white-space: nowrap; overflow: hidden'),E.TD(txt),*(() if unit is None else (E.TD(*uncomp(unit)),)))
    return tostring(E.TABLE(E.TBODY(*rows())),encoding='unicode')

Setup = Setup()

def pname(f):
  return '{}{}'.format(f.__qualname__,inspect.signature(f))

def mro(f):
  import sys
  c = sys.modules[f.__module__]
  try:
    qn = f.__qualname__.split('.')
    for e in qn[:-1]: c = getattr(c,e)
    n = qn[-1]
    if inspect.isclass(c):
      for cc in c.__mro__[1:]:
        if hasattr(cc,n): yield getattr(cc,n)
    else: return
  except:
    return
