import argparse
import re

import numpy as np
import netCDF4 as cdf
import scipy.optimize as spo

def refs_file(fname):
    files = open(fname)
    refs = []
    for ref in files:
        if ref[0] != '#': refs.append( ref.strip() )
    files.close()
    return refs


def get_args():
    # Get command line values
    parser = argparse.ArgumentParser()
    
    # This is a little backwards. If you request no background, this argument gets
    # set to False. That is because of the call to ref_build later.
    parser.add_argument('--nobkg', action='store_const', default=True, const=False,
            help='Turn off the usage of a single  MS slice as a background in \
                    fitting.')
    
    parser.add_argument('--bkg_time', default='0.0',  
            help='The time position of the spectrum to use as a background for \
            fitting. This has no effect if "--nobkg" is used.' )
    
    return parser.parse_args()


class AIAFile(object):
    def __init__(self, fname):
        self.filename = fname
    
        self._AIAproc()

    def _AIAproc(self, ):
        data = cdf.Dataset(self.filename)

        points = data.variables['point_count'][:]
        points_max = points.max()

        times_cdf = data.variables['scan_acquisition_time']
        times = times_cdf[:]/60.

        mass_cdf = np.array( data.variables['mass_values'][:], dtype=int)
        mass_min = mass_cdf.min()
        mass_max = mass_cdf.max()
        masses = np.arange(mass_min, mass_max +1)
        
        inten_cdf = np.array( data.variables['intensity_values'][:],
                dtype=float)

        intens = []
        start = 0
        
        for index in xrange( len(times) ):
            point = points[index]
            time = times[index]
            
            int_zero = np.zeros(masses.size, dtype=float)
            
            if point == 0: 
                intens.append( int_zero )
                continue
                
            mass_tmp = mass_cdf[start:start+point]

            ints = inten_cdf[start:start+point]
            int_zero[mass_tmp - mass_min] = ints

            intens.append( int_zero )

            start += point

        data.close()
        
        self.intensity = np.array(intens)
        self.times = times
        self.masses = masses

        self.tic = self.intensity.sum(axis=1)

    def _ref_extract(self, fname):
        f = open(fname)
    
        m, d = [], []
        for line in f:
            if line[0] == '#': continue
            if line.isspace(): continue
            sp = line.split()
            m.append(sp[0])
            d.append(sp[1])
        f.close()
        
        ref_spec = self._ref_extend(m, d)

        return ref_spec

    def _ref_extend(self, masses, intensities):
        masses = np.array(masses, dtype=int)
        intensities = np.array(intensities, dtype=float)

        spec = np.zeros(self.masses.size, dtype=float)
        spec[masses - self.masses.min()] = intensities
        return spec/spec.max()

    def _txt_file(self, fname):
        files = open(fname)
        refs = []
        for ref in files:
            if ref[0] != '#': refs.append( ref.strip() )
        files.close()
        return refs

    def _msl_file(self, fname):
        regex = r'\(\s*(\d*)\s*(\d*)\)'
        recomp = re.compile(regex)
        
        f = open(fname)

        ref_names = []
        ref_inten = []

        for line in f:
            if 'NAME' in line:
                sp = line.split(':')
                ref_names.append(sp[1])
            elif 'NUM PEAK' in line:
                inten = []
                mass = []
                while not line.isspace():
                    vals = recomp.findall(line)
                    for val in vals:
                        mass.append(val[0])
                        inten.append(val[1])
                    line = next(f)
                ref = self._ref_extend(mass, inten)
                ref_inten.append(ref)
        
        return ref_names, ref_inten
            
    def ref_build(self, ref_file, bkg=True, bkg_time=0.):
        if ref_file[-3:].lower() == 'txt':
            ref_array = []

            files = self._txt_file(ref_file)
            ref_files = [i[:-4] for i in files]

            for f in files:
                temp = self._ref_extract(f)
                ref_array.append( temp )

        if ref_file[-3:].lower() == 'msl':
            ref_files, ref_array = self._msl_file(ref_file)
        
        if bkg == True:
            bkg_idx = np.abs(self.times - bkg_time).argmin()
            ref_array.append( self.intensity[bkg_idx] )
            ref_files.append( 'Background' )
            self._bkg_idx = bkg_idx
        
        self.ref_array = np.array(ref_array)
        self.ref_files = ref_files

    def nnls(self, ):
        fits = []

        for ms in self.intensity:
            fit, junk = spo.nnls(self.ref_array.T, ms)
            fits.append( fit )

        self.fits = np.array( fits )

    def integrate(self, start, stop):
        mask = (self.times > start) & (self.times < stop)
        chunk = self.fits[mask]
        integral = chunk.sum( axis = 0 )

        self.last_int_start = start
        self.last_int_stop = stop
        self.last_int_region = chunk

        return integral

