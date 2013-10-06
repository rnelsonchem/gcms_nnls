import os

import numpy as np
import tables as pyt
import scipy.stats as sps
import matplotlib.pyplot as plt

#import chem.gcms as gcms
import gcms

#### User Modified Values ####

ref_name = 'reference_files.txt'
h5f_name = 'cal.h5'

##############################

class CalTable( pyt.IsDescription ):
    cpd = pyt.StringCol( 50, pos=0 )
    int_start = pyt.Float64Col( pos=1 )
    int_stop = pyt.Float64Col( pos=2 )
    slope = pyt.Float64Col( pos=3 )
    intercept = pyt.Float64Col( pos=4 )
    r = pyt.Float64Col( pos=5 )
    p = pyt.Float64Col( pos=6 )
    stderr = pyt.Float64Col( pos=7 )
    refcol = pyt.Int16Col( pos=8 )
    
refs = gcms.refs_file( ref_name )

h5f = pyt.openFile(h5f_name, 'w', 'GCMS Calibrations')
table = h5f.createTable('/', 'cals', CalTable, )

for n, ref in enumerate(refs):
    name = ref[:-4]
    if not os.path.exists(name + '.csv'):
        continue
    print 'Processing:', name

    csv = open(name+'.csv')

    header = csv.next().split(',')
    start = float(header[3])
    stop = float(header[5])
    
    files = []
    conc = []
    
    for line in csv:
        if line.isspace(): continue
        elif line[0] == '#': continue
        sp = line.split(',')
        files.append( sp[0] )
        conc.append( sp[1] )
    csv.close()

    conc = np.array( conc, dtype=float )

    aias = []
    ints = []

    plt.figure()
    for f in files:
        aia = gcms.AIAFile( os.path.join(name, f) )
        aia.ref_build( refs )
        aia.nnls()
        integral = aia.integrate(start, stop)
        ints.append( integral[n] )
        aias.append( aia )

        plt.plot(aia.times, aia.fits[:, n])

    plt.xlim(start, stop)
    plt.savefig(os.path.join(name, name+'_'+'fits'), dpi=200)
    plt.close()
            
    ints = np.array(ints, dtype=float)
    slope, intercept, r, p, stderr = sps.linregress(conc, ints)

    plt.figure()
    plt.plot(conc, slope*conc + intercept, 'k-')
    plt.plot(conc, ints, 'o', ms=8)
    text_string = 'Slope: {:.2f}\nIntercept: {:.2f}\nR^2: {:.5f}'
    plt.text(30., ints.max()*0.8, text_string.format(slope, intercept, r**2))
    plt.savefig(os.path.join(name, name+'_cal_curve'), dpi=200)
    plt.close()

    row = table.row
    row['cpd'] = name
    row['int_start'] = start
    row['int_stop'] = stop
    row['slope'] = slope
    row['intercept'] = intercept
    row['r'] = r
    row['p'] = p
    row['stderr'] = stderr
    row['refcol'] = n
    row.append()

h5f.flush()
h5f.close()

pyt.copyFile(h5f_name, h5f_name+'temp', overwrite=True)
os.remove(h5f_name)
os.rename(h5f_name+'temp', h5f_name)
