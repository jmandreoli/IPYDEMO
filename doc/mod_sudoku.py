# File:                 demo/odesimu.py
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Illustration of the sudoku subpackage

from IPYDEMO.sudoku import Sudoku
from time import perf_counter

print('**GENERATING a random Sudoku instance**... ',end='',flush=True)
t = perf_counter()
for _ in range(3):
  try: s = Sudoku.generate(N=9,target_density=.35)
  except: continue
  else: break
else: raise Exception('Generation failed after 3 attempts')
elapsed = perf_counter()-t; print(f'Done ({elapsed:.2f}s)')
p = RUN.path('.html'); p.write_text(s._repr_html_())
print(f'''
.. raw:: html
   :file: {p.name}
''')
print('**SOLVING the generated instance**...',end='',flush=True)
s_solved = s.solve()
print()
p = RUN.path('.html','solved'); p.write_text(s_solved._repr_html_())
print(f'''
.. raw:: html
   :file: {p.name}
''')
