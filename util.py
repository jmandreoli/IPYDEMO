def set_helper(*H):
  def transf(f):
    f.helper = H+(f.helper if hasattr(f,'helper') else ())
    return f
  return transf

def set_defaults(**D):
  from functools import wraps, partial
  from collections import ChainMap
  def transf(f):
    p = partial(f,**D)
    @wraps(f)
    def F(*a,**ka): return p(*a,**ka)
    F.defaults = ChainMap(D,f.defaults) if hasattr(f,'defaults') else D
    return F
  return transf

class Helper:
  def __init__(self,*L):
    def trim(x,m=10):
      x = str(x)
      return x if len(x)<=m else '...'
    def h(H,D):
      for x in H:
        p = x.split(':',1)
        yield '{:10}{}: {}'.format(p[0],('({:10})'.format(trim(D[p[0]])) if p[0] in D else ''),p[1]) if len(p)==2 else x
    self.table = '\n'.join('**** {} ****\n    {}'.format(f,'\n    '.join(h(f.helper,f.defaults if hasattr(f,'defaults') else {}))) for f in L)
  def __repr__(self): return self.table
