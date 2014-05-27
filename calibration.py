import os
import argparse
from multiprocessing import Pool

import numpy as np
import tables as pyt
import scipy.stats as sps
import matplotlib.pyplot as plt

#import chem.gcms as gcms
import gcms

# Get the command line arguments
args = gcms.get_args()

# Open the reference file
#refs = gcms.refs_file( args.ref_name )

def cal_h5_build(args):
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
        
    h5f = pyt.openFile(args.cal_name, 'w', 'GCMS Calibrations')
    table = h5f.createTable('/', 'cals', CalTable, )
    # Here I'm storing the background information in case I need to know
    # later.
    table.attrs.bkg = args.nobkg
    table.attrs.bkg_time = args.bkg_time

    return h5f, table

def cal_file(fname):
    f = open(fname)
    next(f)
    
    refs = {}
    ref_files = set()
    for line in f:
        if line[0] == '#': continue
        elif line.isspace(): continue
        line = line.strip()

        sp = line.split(',')
        if sp[0] in refs:
            refs[ sp[0] ].append(sp[1:])
        else:
            refs[ sp[0] ] = [ sp[1:], ]
        ref_files.add(sp[1])

    return refs, list(ref_files)

def aia_build(ref_file, args=args):
    print 'Processing:', ref_file

    aia = gcms.AIAFile( os.path.join(args.cal_folder, ref_file) )

    aia.ref_build(args.ref_name, bkg=args.nobkg,
            bkg_time=float(args.bkg_time))

    aia.nnls()

    return aia

def int_extract(name, refs, aias, args):
    ints = []
    conc = []

    plt.figure()
    for line in refs:
        aia = aias[ line[0] ]
        conc.append( line[1] )
        start, stop = [float(i) for i in line[2:4]]
        n = aia.ref_files.index(name)

        integral = aia.integrate(start, stop)
        ints.append( integral[n] )

        plt.plot(aia.times, aia.fits[:, n])

    plt.xlim(start, stop)
    plt.savefig(os.path.join(args.cal_folder, name+'_'+'fits'), dpi=200)
    plt.close()
            
    ints = np.array(ints, dtype=float)
    conc = np.array(conc, dtype=float)

    return ints, conc

def calibrate(name, args, ints, conc, table):
    slope, intercept, r, p, stderr = sps.linregress(conc, ints)

    plt.figure()
    plt.plot(conc, slope*conc + intercept, 'k-')
    plt.plot(conc, ints, 'o', ms=8)
    text_string = 'Slope: {:.2f}\nIntercept: {:.2f}\nR^2: {:.5f}'
    plt.text(30., ints.max()*0.8, text_string.format(slope, intercept, r**2))
    plt.savefig(os.path.join(args.cal_folder, name+'_cal_curve'), dpi=200)
    plt.close()

    row = table.row
    row['cpd'] = name
#    row['int_start'] = start
#    row['int_stop'] = stop
    row['slope'] = slope
    row['intercept'] = intercept
    row['r'] = r
    row['p'] = p
    row['stderr'] = stderr
#    row['refcol'] = n
    row.append()


if __name__ == '__main__':
    h5f, table = cal_h5_build(args)

    refs, ref_files = cal_file('calibration.csv')

    p = Pool(4)
    aias = p.map(aia_build, ref_files)
#    aias = [aia_build(i) for i in ref_files]

    aias = dict( zip(ref_files, aias) )

    for name in refs:
        ints, conc = int_extract(name, refs[name], aias, args)
        calibrate(name, args, ints, conc, table)


    h5f.flush()
    h5f.close()
    
    pyt.copyFile(args.cal_name, args.cal_name+'temp', overwrite=True)
    os.remove(args.cal_name)
    os.rename(args.cal_name+'temp', args.cal_name)

