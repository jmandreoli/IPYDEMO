import re

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
    if cls.Help_ is None: cls.Help_ = multidisp(cls.Help)
    return cls.Help_

class multidisp:

  def __init__(self,msg):
    msg = parse(msg)
    self.msg_str = '\n'.join('{}{}: {}'.format(a,g_unit(u),h) for a,u,h in msg)
    self.msg_latex = '\\begin{{itemize}}\n{}\n\\end{{itemize}}'.format('\n'.join('\\item {{\bf {}}}{}:{}'.format(a,g_unit(u,superscript='$^{}$'),h) for a,u,h in msg))
    self.msg_html = '<table><tbody>{}</tbody></table>'.format(''.join('<tr><th>{}</th><td>{}</td><td>{}</td></tr>'.format(a,g_unit(u,superscript='<sup>{}</sup>',fmt='{}'),h) for a,u,h in msg))
  def __str__(self): return self.msg_str
  def _repr_latex_(self): return self.msg_latex
  def _repr_html_(self): return self.msg_html

def parse(msg,pat=re.compile(r'(\S+)(?:\s+\[(\S+)\])?:\s+(\S.*)')):
  return [(m.group(1),p_unit(m.group(2)),m.group(3)) for m in (pat.fullmatch(x) for x in (x.strip() for x in msg.split('\n')) if x)]

def g_unit(u,superscript='^{}',fmt=' ({})'):
  return '' if u is None else fmt.format('.'.join((un+superscript.format(ue) if ue!=1 else un) for un,ue in u))

def p_unit(u):
  return None if u is None else tuple((x+(1,) if len(x)==1 else x) for x in (tuple(x.split('^',1)) for x in u.split('.')))
