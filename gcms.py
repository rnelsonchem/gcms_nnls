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
            sp = line.split()
            m.append(sp[0])
            d.append(sp[1])
        f.close()
        
        m = np.array(m, dtype=int)
        d = np.array(d, dtype=float)
    
        ref_spec = np.zeros(self.masses.size, dtype=float)
        ref_spec[m - self.masses.min()] = d
        ref_spec = ref_spec/ref_spec.max()
        
        return ref_spec

    def ref_build(self, files, bkg=True, bkg_time=0.):
        ref_array = []
        ref_files = [i[:-4] for i in files]

        for f in files:
            temp = self._ref_extract(f)
            ref_array.append( temp )
        
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

