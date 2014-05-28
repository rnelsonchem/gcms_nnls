from __future__ import unicode_literals

import argparse
import re
from codecs import open

import numpy as np
import netCDF4 as cdf
import scipy.optimize as spo
import pandas as pds

def get_args():
    # Get command line values
    parser = argparse.ArgumentParser()
    
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


class AIAFile(object):
    def __init__(self, fname):
        self.filename = fname
    
        self._AIAproc()

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
                
            mass_tmp = mass_cdf[start:start+point]
            ints_tmp = inten_cdf[start:start+point]
            
            df_dict = {'round': np.round(mass_tmp).astype(int, copy=False), 
                    'ints': ints_tmp}
            df = pds.DataFrame(df_dict)
            group = df.groupby('round').mean()

            mass_tmp2 = np.asarray(group.index, dtype=int)
            ints_tmp2 = np.asarray(group)
            
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
            elif 'NAME' in line:
                sp = line.split(':')
                name = sp[1].strip()
                self.ref_files.append(name)
                self.ref_meta[name] = {}
                self._txt_ref(f, name=name)

    def _txt_ref(self, fobj, name):
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
                    vals = line.split()
                    mass.append(vals[0])
                    inten.append(vals[1])

                ref = self._ref_extend(mass, inten)
                self.ref_array.append(ref)
                if space:
                    return None

            elif not space:
                meta = line.split(':')
                self.ref_meta[name][meta[0]] = meta[1].strip()

            if space:
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
                while not space:
                    vals = recomp.findall(line)
                    for val in vals:
                        mass.append(val[0])
                        inten.append(val[1])
                    line = next(fobj)
                    space = line.isspace()
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


    def nnls(self, ):
        fits = []

        for ms in self.intensity:
            fit, junk = spo.nnls(self.ref_array.T, ms)
            fits.append( fit )

        self.fits = np.array( fits )


    def integrate(self, start, stop):
        mask = (self.times > start) & (self.times < stop)

        chunk = self.fits[mask]
        fit_ms = chunk[:,:,np.newaxis]*self.ref_array
        
        integral = fit_ms.sum( axis = (0,2) )

        self.last_int_start = start
        self.last_int_stop = stop
        self.last_int_mask = mask
        self.last_int_fits = chunk
        self.last_int_ms = fit_ms
        self.integral = integral

        return integral

