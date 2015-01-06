from __future__ import unicode_literals

import os
import argparse
import re
from codecs import open
import itertools as it

import numpy as np
import netCDF4 as cdf
import scipy.optimize as spo

class AIAFile(object):
    def __init__(self, fname):
        self.filename = fname
    
        self._AIAproc()

    def _groupkey(self, x):
        return x[0]

    def _AIAproc(self, ):
        data = cdf.Dataset(self.filename)

        points = data.variables['point_count'][:]

        times_cdf = data.variables['scan_acquisition_time']
        times = times_cdf[:]/60.

        mass_cdf = data.variables['mass_values'][:]
        mass_min = np.int( np.round( mass_cdf.min() ) )
        mass_max = np.int( np.round( mass_cdf.max() ) )
        masses = np.arange(mass_min, mass_max +1)
        
        inten_cdf = data.variables['intensity_values'][:]

        intens = []
        start = 0
        
        for point in points:
            int_zero = np.zeros(masses.size, dtype=float)
            
            if point == 0: 
                intens.append( int_zero )
                continue
                
            mass_tmp = np.round( mass_cdf[start:start+point] ).astype(int)
            ints_tmp = inten_cdf[start:start+point]
            
            mass_tmp2 = []
            ints_tmp2 = []
            for mass, mass_int in it.groupby( zip(mass_tmp, ints_tmp),
                    key=self._groupkey):
                ints = [i[1] for i in mass_int]
                if len(ints) > 1:
                    ints = np.array( ints ).mean()
                else:
                    ints = ints[0]
                mass_tmp2.append(mass)
                ints_tmp2.append(ints)
            mass_tmp2 = np.array(mass_tmp2)
            ints_tmp2 = np.array(ints_tmp2)
                    
            mask = mass_tmp2 - mass_min
            int_zero[mask] = ints_tmp2

            intens.append( int_zero )

            start += point

        data.close()
        
        self.intensity = np.array(intens)
        self.times = times
        self.masses = masses

        self.tic = self.intensity.sum(axis=1)


    def _ref_extend(self, masses, intensities):
        masses = np.array(masses, dtype=int)
        intensities = np.array(intensities, dtype=float)
        mask = (masses > self.masses.min()) & (masses < self.masses.max())
        masses = masses[mask] - self.masses.min()
        intensities = intensities[mask]

        spec = np.zeros(self.masses.size, dtype=float)
        spec[masses] = intensities
        return spec/spec.max()

    def _txt_file(self, fname):
        f = open(fname)

        for line in f:
            if line[0] == '#': continue
            elif line.isspace(): continue

            sp = line.split(':')
            sp = [i.strip() for i in sp]
            
            if sp[0] == "NAME":
                name = sp[1]
                self.ref_files.append(name)
                self.ref_meta[name] = {}
            elif sp[0] == "NUM PEAKS":
                line = self._txt_ref(f, name=name)
                if line:
                    sp = line.split(":")
                    sp = [i.strip() for i in sp]
                    self.ref_meta[name][sp[0]] = sp[1]
            else:
                self.ref_meta[name][sp[0]] = sp[1]

    def _txt_ref(self, fobj, name):
        inten = []
        mass = []

        for line in fobj:
            if line[0] == '#': continue
            elif line.isspace(): break
            elif ":" in line: 
                return line

            vals = line.split()
            mass.append(vals[0])
            inten.append(vals[1])

        ref = self._ref_extend(mass, inten)
        self.ref_array.append(ref)

        return None


    def _msl_file(self, fname, encoding):
        regex = r'\(\s*(\d*)\s*(\d*)\)'
        recomp = re.compile(regex)
        
        f = open(fname, encoding=encoding)

        for line in f:
            if line[0] == '#': continue
            elif 'NAME' in line:
                sp = line.split(':')
                name = sp[1].strip()
                self.ref_files.append(name)
                self.ref_meta[name] = {}
                self._msl_ref(f, name=name, recomp=recomp)


    def _msl_ref(self, fobj, name, recomp):
        for line in fobj:
            if line[0] == '#': continue
            space = line.isspace()

            if 'NUM PEAK' in line:
                inten = []
                mass = []
                for line in fobj:
                    if line.isspace():
                        space = True
                        break
                    vals = recomp.findall(line)
                    for val in vals:
                        mass.append(val[0])
                        inten.append(val[1])
                ref = self._ref_extend(mass, inten)
                self.ref_array.append(ref)
                if space:
                    return None

            elif not space:
                meta = line.split(':')
                self.ref_meta[name][meta[0]] = meta[1].strip()

            if space:
                return None

            
    def ref_build(self, ref_file, bkg=True, bkg_time=0., encoding='ascii'):
        self.ref_array = []
        self.ref_files = []
        self.ref_meta = {}

        if ref_file[-3:].lower() == 'txt':
            self._txt_file(ref_file)

        if ref_file[-3:].lower() == 'msl':
            self._msl_file(ref_file, encoding)
        
        if bkg == True:
            bkg_idx = np.abs(self.times - bkg_time).argmin()
            bkg = self.intensity[bkg_idx]/self.intensity[bkg_idx].max()
            self.ref_array.append( bkg )
            self.ref_files.append( 'Background' )
            self._bkg_idx = bkg_idx
        
        self.ref_array = np.array(self.ref_array)


    def nnls(self, rt_filter=False, rt_win=0.2, rt_adj=0.):
        fits = []
        
        # If a retention time filter is requested, then build up an array of
        # retention times from the meta data
        if rt_filter == True:
            rts = []
            for name in self.ref_files:
                if name == 'Background':
                    rts.append( -5. )
                    continue
                rt = self.ref_meta[name]['RT']
                rts.append(rt)
            self.ret_times = np.array(rts, dtype=float)

        for time, ms in zip(self.times, self.intensity):
            # If no retention time filter, just do standard fit
            if rt_filter == False:
                fit, junk = spo.nnls(self.ref_array.T, ms)

            else:
                # Create a boolean RT filter mask
                mask = ((self.ret_times + rt_adj) > (time - rt_win)) & \
                        ((self.ret_times + rt_adj) < (time + rt_win))
                zeros = np.zeros( len(self.ref_files) )
                # Check if the filter has any hits
                msum = mask.sum()
                if msum != 0:
                    if self.ref_files[-1] == 'Background':
                        mask[-1] = True
                    ref_arr = self.ref_array[mask]
                    fit, junk = spo.nnls(ref_arr.T, ms)
                    zeros[mask] = fit
                    fit = zeros
                # If no RT hits, fit the data with either the background or
                # use only zeros
                else:
                    if self.ref_files[-1] == 'Background':
                        fit, junk = spo.nnls(self.ref_array[-1].reshape(-1,1)
                                , ms)
                        zeros[-1] = fit[0]
                    fit = zeros

            fits.append( fit )

        self.fits = np.array( fits )


    def integrate(self, start, stop):
        mask = (self.times > start) & (self.times < stop)
        self.last_int_start = start
        self.last_int_stop = stop

        chunk = self.fits[mask]
        self.last_int_mask = mask
        self.last_int_fits = chunk

        fit_ms = chunk[:,:,np.newaxis]*self.ref_array
        self.last_int_ms = fit_ms

        sim = fit_ms.sum(axis=2)
        self.last_int_sim = sim
        
        integral = fit_ms.sum( axis = (0,2) )
        self.integral = integral

#### General Functions ####


def clear_png(folder):
    for f in os.listdir(folder):
        if f[-3:] == 'png':
            os.remove( os.path.join(folder, f) )


def get_args():
    # Get command line values
    parser = argparse.ArgumentParser()

    parser.add_argument('--nproc', default=1,  type=int,
            help='The number of cores to use for processing.')

    # This is a little backwards. If you request no background, this argument
    # gets set to False. That is because of the call to ref_build later.
    parser.add_argument('--nobkg', action='store_const', default=True,
            const=False, help='Turn off the usage of a single  MS slice as a \
            background in fitting.')
    
    parser.add_argument('--bkg_time', default='0.0',  
            help='The time position of the spectrum to use as a background for \
            fitting. This has no effect if "nobkg" is used.' )
    
    parser.add_argument('--ref_name', default='ref_specs.txt',  
            help='The name of the file that contains the reference spectra.')
    
    parser.add_argument('--cal_name', default='cal.h5',  
            help='The name of the calibration HDF file.')
    
    parser.add_argument('--cal_folder', default='calibration',  
            help='The folder that contains the calibration files.')

    parser.add_argument('--data_name', default='data.h5',  
            help='The name of the processed data HDF file.')

    parser.add_argument('--data_folder', default='data',  
            help='The name of folder containing the data files.')
    
    parser.add_argument('--cal_type', default='conc',  
            help='The type of calibration that was done for these samples. \
            conc = Typical concentration curve; internal = internal standard.')

    parser.add_argument('--standard', default='octane',  
            help='The internal standard used for calibration. Only used if \
            cal_type == "internal".')

    parser.add_argument('--std_start', default=7.0,  type=float,
            help='The start time for integration of the internal standard. \
            Only valid if cal_type == "internal".')

    parser.add_argument('--std_stop', default=7.4,  type=float,
            help='The stop time for integration of the internal standard. \
            Only valid if cal_type == "internal".')

    return parser.parse_args()


def table_check(table, args):
    # Warn if background info is not the same for calibrations and data analysis
    if table.attrs.bkg != args.nobkg:
        if table.attrs.bkg == True:
            print \
'''Warning: Your calibration data was run with a background subtraction. 
This may affect the analysis values.
'''

        else:
            print \
'''Warning: Your calibration data was not run with a background subtraction.
This may affect the analysis values.
'''

    elif table.attrs.bkg_time != args.bkg_time:
        warning = \
'''Warning: The time for your background spectrum does not match the
calibration data. This may affect the values of your analysis.
Calibration background time = {}
Data background time = {}
'''
        print warning.format(table.attrs.bkg_time, args.bkg_time)
    
    if table.attrs.cal_type == 'internal' or args.cal_type == 'internal':
        if table.attrs.cal_type != args.cal_type:
            warning =  \
'''The calibration types do not match!
Current selection: {}
Used for calibration: {}
Type changed to saved value from calibration data.
'''
            print warning.format(args.cal_type, table.attrs.cal_type)
            args.cal_type = table.attrs.cal_type
        
        if table.attrs.std_start != args.std_start or \
                table.attrs.std_stop != args.std_stop:
            warning = \
'''Internal standard integration times are mismatched.
Cal start {:.3f}: Selected Start {:.3f}
Cal stop  {:.3f}: Selected Stop {:.3f}
Values changed to saved values from calibration data.
'''
            print warning.format(table.attrs.std_start, args.std_start,
                    table.attrs.std_stop, args.std_stop)
            args.std_start = table.attrs.std_start
            args.std_stop = table.attrs.std_stop
    


