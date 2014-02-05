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

# Get the command line arguments
args = gcms.get_args()

# Process the file with the referece file names
refs = gcms.refs_file(ref_name)

# Open the calibration data file
cal = pyt.openFile(cal_name)
cal_table = cal.root.cals

# Warn if background info is not the same for calibrations and data analysis
if cal_table.attrs.bkg != args.nobkg:
    if cal_table.attrs.bkg == True:
        print \
'''Warning: Your calibration data was run with a background subtraction. 
This may affect the analysis values.
'''

    else:
        print \
'''Warning: Your calibration data was not run with a background subtraction.
This may affect the analysis values.
'''

elif cal_table.attrs.bkg_time != args.bkg_time:
    warning = \
'''Warning: The time for your background spectrum does not match the
calibration data. This may affect the values of your analysis.
Calibration background time = {}
Data background time = {}
'''
    print warning.format(cal_table.attrs.bkg_time, args.bkg_time)

# Make a new hdf5 file for data from sample runs
h5f = pyt.openFile(data_name, 'w', 'Catalytic Runs')

cal_cpds = [i[0] for i in cal_table]
col_dict = {cal_cpd: pyt.Float64Col() for cal_cpd in cal_cpds}
col_dict['fname'] = pyt.StringCol(255, pos=0)

col_dict2 = col_dict.copy()
for cal_cpd in cal_cpds:
    col_dict2[ cal_cpd+'_per' ] = pyt.Float64Col()
col_dict2['cpd_name'] = pyt.StringCol(255, pos=1)

int_table = h5f.createTable('/', 'int_data', col_dict2, "Raw Integration Data")
int_table.attrs.bkg = args.nobkg
int_table.attrs.bkg_time = args.bkg_time

data_table = h5f.createTable('/', 'conc_data', col_dict, "Concentration Data")

files = os.listdir(data_folder)
files = [f for f in files if f[-3:] == 'CDF']

for f in files:
    name = f[:-4]
    print 'Processing:', f

    aia = gcms.AIAFile( os.path.join(data_folder, f) )
    aia.ref_build(refs, bkg=args.nobkg, bkg_time=float(args.bkg_time) )
    aia.nnls()

    row = data_table.row
    row['fname'] = name

    for cpd in cal_table:
        cpd_name = cpd[0]
        start, stop = cpd[1], cpd[2]
        slope, intercept = cpd[3], cpd[4]
        column = cpd[8]

        ints = aia.integrate( start, stop )
        ints_sum = ints.sum()
        int_row = int_table.row
        int_row['fname'] = name
        int_row['cpd_name'] = cpd_name
        for n, cal_cpd in enumerate(cal_cpds):
            int_row[ cal_cpd ] = ints[n]
            int_row[ cal_cpd+'_per' ] = ints[n]/ints_sum
        int_row.append()
        
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
