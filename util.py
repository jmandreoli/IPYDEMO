import re
from collections import OrderedDict

#==================================================================================================
class HelpPlugin:
  r"""
Add this plugin to the inheritance hierarchy of a class and configure a class attribute :attr:`Help` in that class or subclasses. Then call method :meth:`helper` on instances to obtain a help object which can be displayed in various formats.
  """
#==================================================================================================

  Help = ''
  Help_ = None
  r"""Should contain a list of triples, where each triple consists of a topic string, a unit, and help string. The unit is itself either :const:`None` or a list of pairs, where each pair consists of the name of a unit and an exponent."""

#--------------------------------------------------------------------------------------------------
  @classmethod
  def helper(cls):
    r"""
Displays a short helper attached to class *cls*. Use class attribute :attr:`Help` to configure it.
    """
#--------------------------------------------------------------------------------------------------
    if cls.Help_ is None: cls.Help_ = multidisp(parse(cls))
    return cls.Help_

class multidisp:

  def __init__(self,D): self.D = D
  def __str__(self): return self.D['']
  def _repr_latex_(self): return self.D.get('latex')
  def _repr_html_(self): return self.D.get('html')

def parse(cls,pat=re.compile(r'(\S+)(?:\s+\[(\S+)\])?:\s+(\S.*)')):
  L = OrderedDict()
  pre = '{}.{}'.format(cls.__module__,cls.__name__)
  for x in cls.Help.split('\n'):
    x = x.strip()
    if not x: continue
    m = pat.fullmatch(x)
    h = p_unit(m.group(2)),m.group(3)
    a,p = m.group(1).split('/',1)
    if a=='': a = pre
    else: assert hasattr(cls,a); a = '{}:{}'.format(pre,a)
    if not a in L: L[a] = OrderedDict()
    L[a][p] = h
  D = {}
  D[''] = '\n'.join(a+'\n'+'\n'.join('\t{}{}: {}'.format(p,g_unit(u),h) for p,(u,h) in P.items()) for a,P in L.items())
  D['latex'] = latexlist(latexesc(a)+'\n'+latexlist('{}{}: {}'.format(latexesc(p),g_unit(u,superscript='$^{}$'),h) for p,(u,h) in P.items()) for a,P in L.items())
  D['html'] = '<table style="background-color: white; color: black;"><tbody>{}</tbody></table>'.format(''.join('<tr style="background-color: gray; color: white;"><th colspan="3">{}</th></tr>{}'.format(a,''.join('<tr><th>{}</th><td>{}</td><td>{}</td></tr>'.format(p,g_unit(u,superscript='<sup>{}</sup>',fmt='{}'),h) for p,(u,h) in P.items())) for a,P in L.items()))
  return D

def g_unit(u,superscript='^{}',fmt=' ({})'):
  return '' if u is None else fmt.format('.'.join((un+superscript.format(ue) if ue!=1 else un) for un,ue in u))

def p_unit(u):
  return None if u is None else tuple((x+(1,) if len(x)==1 else x) for x in (tuple(x.split('^',1)) for x in u.split('.')))

def latexesc(x): return x.replace('_',r'\_')

def latexlist(L): return '\\begin{{itemize}}\n{}\n\\end{{itemize}}'.format('\n'.join('\item {}'.format(x) for x in L))
