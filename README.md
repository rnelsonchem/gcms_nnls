# GCMS AIA File Import and Non-negative Least squares

These programs serve two roles: 1) to open standard GCMS AIA data files, and
2) to fit the data using non-negative least squares with a series of reference
spectra. 

## Getting started

In addition to downloading the files in this repository, you will also need a
fairly complete Python 2.7 installation with the libraries Numpy (v 1.9.1
tested), matplotlib (v 1.4.2 tested), netCDF4 (v 1.0.4 tested), PyTables (v
3.1.1 tested), and Scipy (v 0.14.0 tested). In addition, although not
required, these programs are meant to run interactively through the use of the
advanced Python interpreter IPython (v 2.3.1 tested), and examples in this
documentation assume that you are using this environment.  Installing all of
these packages can be a little daunting for a novice, so it is best to start
with an all-in-one package. In this case, the [Anaconda Python
distribution](http://continuum.io/downloads) is a very nice option. It
combines a large number of Python packages for scientific data analysis, and
in addition to a number of useful features, it can also take care of software
updates for you. The Anaconda developers (Continuum Analytics) have a lot of
useful documentation for [Anaconda](http://docs.continuum.io/anaconda/) (which
is the collection of Python packages) and
[conda](http://conda.pydata.org/docs/) (the actual package management
program). On Windows, Anaconda may not install netCDF4. In this case, you can
get a prebuilt installer from [Christoph
Gohlke](http://www.lfd.uci.edu/~gohlke/pythonlibs/): you will want the Python
2.7 ("cp27") 64-bit ("amd64") build for the most recent version. Getting
started with the installation and usage of these packages is covered in many
places on the internet, so it is not covered here.

The usage of these programs is outlined in the user guide ("USERGUIDE.md" or
"USERGUIDE.pdf"). 

