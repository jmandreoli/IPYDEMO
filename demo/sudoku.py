# File:                 demo/odesimu.py
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Illustration of the sudoku subpackage
from make import RUN; RUN(__name__,__file__) # doc gen trick
#--------------------------------------------------------------------------------------------------

from IPYDEMO.sudoku import Sudoku
from time import perf_counter

def rst(s):
  # returns a RST format representation of the grid
  def rows():
    yield s.N*'+-------'+'+'
    for r,r_ in zip(s.grid,s.source):
      yield ''.join(f'| {f'``{k+1}``' if k_ else f'  {k+1}  ' if k>=0 else '     '} ' for k,k_ in zip(r,r_))+'|'
      yield s.N*'+-------'+'+'
  return f'.. table:: {s}\n\n{'\n'.join('   '+x for x in rows())}'
print()
print('**GENERATING a random Sudoku instance**... ',end='',flush=True)
t = perf_counter()
for _ in range(3):
  try: s = Sudoku.generate(N=9,target_density=.35)
  except: continue
  else: break
else: raise Exception('Generation failed after 3 attempts')
elapsed = perf_counter()-t; print(f'Done ({elapsed:.2f}s)')
print()
print(rst(s))
print()
RUN.pause()
print('**SOLVING the generated instance**...',end='',flush=True)
s_solved = s.solve()
print(f'Done')
print()
print(rst(s_solved))
RUN.pause()