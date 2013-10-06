import os

import numpy as np
import tables as pyt
import matplotlib.pyplot as plt

#import chem.gcms as gcms
import gcms

#### User Modified Values ####

ref_name = 'reference_files.txt'
cal_name = 'cal.h5'
data_name = 'data.h5'
data_folder = 'data'

##############################

refs_file = open(ref_name)
refs = []
for ref in refs_file:
    if ref[0] != '#': refs.append( ref.strip() )
refs_file.close()

cal = pyt.openFile(cal_name)
cal_table = cal.root.cals

h5f = pyt.openFile(data_name, 'w', 'Catalytic Runs')

col_dict = {ref[:-4]: pyt.Float64Col() for ref in refs}
col_dict['fname'] = pyt.StringCol(255, pos=0)

data_table = h5f.createTable('/', 'Concentration data', col_dict)

files = os.listdir(data_folder)
files = [f for f in files if f[-3:] == 'CDF']

for f in files:
    name = f[:-4]
    print 'Processing:', f

    aia = gcms.AIAFile( os.path.join(data_folder, f) )
    aia.ref_build( refs )
    aia.nnls()

    row = data_table.row
    row['fname'] = name
    for cpd in cal_table:
        cpd_name = cpd[0]
        start, stop = cpd[1], cpd[2]
        slope, intercept = cpd[3], cpd[4]
        column = cpd[8]
        ints = aia.integrate( start, stop )
        conc = (ints[column] - intercept)/slope
        
        row[ cpd_name ] = conc

        fit_max = aia.last_int_region.max()

        mask = (aia.times > start) & (aia.times < stop)
        tic_max = aia.tic[mask].max()

        plt.figure()
        plt.plot(aia.times, aia.fits[:,column])
        plt.plot(aia.times, aia.tic*fit_max*1.2/tic_max, 'k', color='0.5')
        plt.xlim(start, stop)
        plt.ylim(ymax=fit_max*1.5)
        plt.title('Concentration = {:.2f}'.format(conc))
        plt.savefig( os.path.join(data_folder, name+'_'+cpd_name), dpi=200 )
        plt.close()

    row.append()

cal.close()

h5f.flush()
h5f.close()

pyt.copyFile(data_name, data_name+'temp', overwrite=True)
os.remove(data_name)
os.rename(data_name+'temp', data_name)
