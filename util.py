from functools import wraps, partial
from collections import OrderedDict
import inspect, re

def Setup(*H,**D):
  def parse(h,pat=re.compile(r'(?P<argn>(?:\w|,)+?)\s*:\s+(?P<help>[^[]+)(?:\s+\[(?P<unit>(?:\w+(?:\^-?[0-9]+)?)(?:\.\w+(?:\^-?[0-9]+)?)*)\])?'),upat=re.compile(r'(?P<base>[^\^]+)(?:\^(?P<expn>.+))?')):
    def unit(x):
      g = upat.fullmatch(x).groups()
      return g[0],(1 if g[1] is None else int(g[1]))
    g = pat.fullmatch(h.strip()).groups()
    return tuple(g[0].split(',')),(g[1],(() if g[2] is None else tuple(unit(x) for x in g[2].split('.'))))
  def tr(f):
    assert inspect.isfunction(f)
    F = (lambda F: wraps(f)(lambda *a,**ka: F(*a,**ka)))(partial(f,**D)) if D else f
    F.setup = H,D
    return F
  H = OrderedDict(map(parse,H))
  return tr

class display:

  def __init__(self,*L): self.L = L

  def _repr_html_(self):
    from lxml.builder import E
    from lxml.etree import tostring
    def row(f,H,D):
      yield E.TR(E.TD(pname(f),colspan='4',style='background-color: gray; color: white; font-weight: bold;'))
      for argn,(txt,unit) in H.items():
        dv = ','.join(repr(D[a]) if a in D else '' for a in argn) if any(a in D for a in argn) else ''
        yield E.TR(E.TH(','.join(argn)),E.TD(dv,style='max-width:2cm; white-space: nowrap; overflow: hidden',title=dv),E.TD(txt),E.TD(*uncomp(unit)))
    def uncomp(u):
      for base,expn in u:
        yield ' '
        yield E.SPAN(base)
        if expn!=1: yield E.SUP(str(expn))
    return tostring(E.TABLE(E.TBODY(*rows(self.L,row))),encoding='unicode')

  def __repr__(self):
    def row(f,H,D,trim=(lambda x: repr(x)[:10])):
      yield '**** {} ****'.format(pname(f))
      for argn,(txt,unit) in H.items():
        dv = '({:10})'.format(','.join(trim(D[a]) if a in D else '' for a in argn)) if any(a in D for a in argn) else ''
        unit = '' if unit is None else ' [{}]'.format('.'.join('{}{}'.format(x[0],('^{}'.format(x[1]) if x[1]!=1 else '')) for x in unit))
        yield '    {:10}{}: {}{}'.format(','.join(argn),dv,txt,unit)
    return '\n'.join(rows(self.L,row))

Setup.display = display

def rows(L,row):
  for x in L:
    if inspect.isfunction(x): yield from row(x,*x.setup)
    elif inspect.isclass(x):
      for name,f in inspect.getmembers(x,inspect.isfunction):
        s = setup(x,name)
        if s is None: continue
        yield from row(f,*s)
    else: raise TypeError('expected: function|class; found: {}'.format(type(x)))

def setup(c,name):
  HH = OrderedDict(); DD = dict()
  for cc in reversed(c.__mro__):
    if hasattr(cc,name):
      f = getattr(cc,name)
      if hasattr(f,'setup'): H,D = f.setup; HH.update(H); DD.update(D)
  return (HH,DD) if HH or DD else None

def pname(f):
  return '{}{}'.format(f.__qualname__,inspect.signature(f))
