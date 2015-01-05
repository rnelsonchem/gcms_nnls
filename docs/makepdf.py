'''Convert the markdown docs to PDF format.

Requires Python 2.7, pandoc, and pdflatex.'''

import os 
import subprocess as sub

try:
    sub.call(['pandoc', '--standalone', '-t', 'latex', '-o', 'USERGUIDE.tex',
            '-r', 'markdown', 'USERGUIDE.md'])
    sub.call(['pdflatex', 'USERGUIDE.tex'])
    sub.call(['pdflatex', 'USERGUIDE.tex'])
except:
    print("There was an exception in pandoc or pdflatex.")
else:
    tex_files = ['.aux', '.log', '.out', '.tex']
    [os.remove('USERGUIDE' + i) for i in tex_files]

