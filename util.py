from functools import wraps, partial
from collections import OrderedDict
import inspect, re

#==================================================================================================
def Setup(*H,**D):
#==================================================================================================
  def parse(h,pat=re.compile(r'(?P<argn>(?:\w|,)+?)\s*:\s+(?P<help>[^[]+)(?:\s+\[(?P<unit>(?:\w+(?:\^-?[0-9]+)?)(?:\.\w+(?:\^-?[0-9]+)?)*)\])?'),upat=re.compile(r'(?P<base>[^\^]+)(?:\^(?P<expn>.+))?')):
    def unit(x):
      g = upat.fullmatch(x).groups()
      return g[0],(1 if g[1] is None else int(g[1]))
    g = pat.fullmatch(h.strip()).groups()
    return tuple(g[0].split(',')),(g[1],(() if g[2] is None else tuple(unit(x) for x in g[2].split('.'))))
  def tr(f):
    assert inspect.isfunction(f)
    if D:
      @wraps(f)
      def F(*a,**ka):
        for k,v in D.items(): ka.setdefault(k,v)
        return f(*a,**ka)
    else: F = f
    F.setup = H_,D_
    return F
  H_,D_ = OrderedDict(),{}
  for h in H:
    if isinstance(h,str): k,v = parse(h); H_[k] = v
    else: H_.update(h.setup[0]); D_.update(h.setup[1])
  D_.update(D)
  return tr

#==================================================================================================
class display:
#==================================================================================================

  def __init__(self,*L): self.L = L

  def _repr_html_(self):
    from lxml.builder import E
    from lxml.etree import tostring
    def row(f):
      yield E.TR(E.TD(pname(f),colspan='4',style='background-color: gray; color: white; font-weight: bold;'))
      H,D = f.setup
      for argn,(txt,unit) in H.items():
        dv = ','.join(repr(D[a]) if a in D else '' for a in argn) if any(a in D for a in argn) else ''
        yield E.TR(E.TH(','.join(argn)),E.TD(dv,style='max-width:2cm; white-space: nowrap; overflow: hidden',title=dv),E.TD(txt),E.TD(*uncomp(unit)))
    def uncomp(u):
      for base,expn in u:
        yield ' '
        yield E.SPAN(base)
        if expn!=1: yield E.SUP(str(expn))
    return tostring(E.TABLE(E.TBODY(*(r for x in functions(self.L) for r in row(x)))),encoding='unicode')

  def __repr__(self):
    def row(f):
      yield '**** {} ****'.format(pname(f))
      H,D = f.setup
      for argn,(txt,unit) in H.items():
        dv = '({:10})'.format(','.join(trim(D[a]) if a in D else '' for a in argn)) if any(a in D for a in argn) else ''
        unit = '' if unit is None else ' [{}]'.format('.'.join('{}{}'.format(x[0],('^{}'.format(x[1]) if x[1]!=1 else '')) for x in unit))
        yield '    {:10}{}: {}{}'.format(','.join(argn),dv,txt,unit)
    trim = lambda x: repr(x)[:10]
    return '\n'.join(r for x in functions(self.L) for r in row(x))

Setup.display = display

#==================================================================================================
# Utilities
#==================================================================================================

def pname(f):
  return '{}{}'.format(f.__qualname__,inspect.signature(f))

def functions(L):
  for x in L:
    if inspect.isfunction(x): yield x
    elif inspect.isclass(x):
      for name,f in inspect.getmembers(x,inspect.isfunction):
        if hasattr(f,'setup'): yield f
    else: raise TypeError('expected: function|class; found: {}'.format(type(x)))
