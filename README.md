# GCMS AIA File Import and Non-negative Least squares

These programs will open a standard GCMS AIA data file and perform
non-negative least squares using a series of reference spectra. All of these
files should be contained in the same folder as the data. This folder needs to
be well structured, as described below.

## Reference MS Files

First of all, you are going to need a series of reference MS spectra to do the
fitting. I got my references from [massBank](http://www.massbank.jp/?lang=en).
The format of these files is important, so a couple of examples are provided
in this repository (refcpd.txt and refcpd2.txt). The most important aspect of
these file is that there are two space-separated data points per line. The
first data point is the mass and the second data point is an intensity. (The
intensities are normalized in the fitting program, so it is not necessary to
make those adjustments yourself.) Comments can be added by starting a line
with '#'. This must be the first character; don't put white space before this
symbol. Use comment lines to keep track of where the MS data was acquired and
any identifying data.

To use these files for fitting, they need to be added to the file
'reference\_files.txt'. Again, an example of this file is provided. The
ordering of compounds in this file is important. Any time you make changes to
this file, you must rerun both calibration.py and data.py to regenerate the
data files that are created by these programs.

## Calibration Data

If you have calibration data for a particular reference compound, you must
create a csv file and folder that have the same base name as the reference MS
file from above. Again, an examples are provided in this repository called
refcpd.csv and the folder refcpd. All of your calibration AIA files for this
compound need to be stored in the newly created folder. In order for these new
data files to be processed, the refcpd.csv file must be appropriately
modified. 

The csv file is a simple comma-separated text file, but again the structure is
important. The first row in this file is critical. At the end, there are two
values that define the starting and stopping time points for integration.
Change these values based on the time range that you've determined from the
TIC of a calibration run. The rest of the rows are data file information.  The
first column is the name of a calibration data file, and the second column
needs to be the concentration of the reference compound associated with that
run. You don't have to add all of the calibration files here, but if they are
not in this list, they won't be processed.  Alternatively, any line that
starts with a '#' is a comment, and will be ignored. In this way, you can
comment out samples, and add some notes as to why that sample was not used or
whatever.

## Run Calibrations

Once you've updated the calibration information from above. You can run the
program 'calibration.py'. This runs through all of the reference spectra
defined in the 'reference\_files.txt' file. If a '.csv' file exists for a
particular reference file, then a calibration will be performed. 

All of the calibration data files listed in the csv file  will be processed
and a calibration curve generated. For each calibration sample, a plot of the
reference-extracted data will be generated in the calibration folder
(refcpd\_fits.png). In addition, a calibration curve plot is also generated
(refcpd\_cal\_curve.png'), which plots the integrated intensities and
calibrated intensities vs the concentrations. In addition, the calibration
information is printed on the graph for quick visual inspection. There is no
need to write down this calibration information.

This program has some important command line arguments that will change the
programs defaults. The first argument, '--nobkg', is a simple flag for
background fitting. By default, the fitting routine will select a MS slice
from the data set and use that as a background in the non-negative least
squares fitting. This procedure can change the integrated values. If you use
this flag, then a background MS will not be used in the fitting. Using a
background slice in the fitting may or may not give good results. It might be
a good idea to look at your data with and without the background subtraction
to see which is better.

The second command line argument is '--bkg\_time'. By default, the fitting
program uses the first MS slice as a background for fitting.  However, if
there is another time that looks like it might make a better background for
subtraction, then you can put that number here. 

Here's a couple of example usages of this script:

    # This will run the calibration program with all defaults
    $ python calibration.py
    # This shuts off the background subtraction
    $ python calibration.py --nobkg
    # This sets an alternate time for the background subtraction
    # In this case, the time is set to 0.12 minutes
    $ python calibration.py --bkg_time 0.12

Another file is also generated during this process: cal.h5. This is a HDF5
file that contains all of the calibration information for each standard. Do
not delete this file; it is essential for the next step. This is a very simple
file, and there are many tools for looking at the internals of an HDF5 file.
For example, [ViTables](http://vitables.org/) is recommended. The background
information, such as whether a background was used and the time point to use
as a background spectrum, are stored as user attributes of the calibration
table.

## Process Sample Data

Put all of your data files in a folder that must be called 'data'. Once you've
done this, run the program 'data.py' to process every AIA data file in that
folder using the calibration information that was determined from the steps
above. 

This program opens the AIA file for the sample and performs non-negative least
squares analysis of the full data set using the reference spectra that are
listed in the 'reference\_files.txt' file. Using the calibration information
that was determined above, it finds the concentrations of those components in
the sample data. For every reference compound that has associated calibration
information, a plot is generated that overlays the TIC (gray) and extracted
reference fit (blue). The title of the plot provides the calibrated
concentration information. Visual inspection of these files is recommended. 

This file also accepts the same command line arguments as 'calibration.py'
from the section above. You will be warned if you try to analyze your data
with different background information than the calibration samples. This may
not impact your data much, but it is good to know if you are doing something
different.

This file also generates another HDF5 file called 'data.h5', which contains
the integration and concentration information for every component. This
information is identical to what is printed on the extraction plots above.
However, this tabular form of the data is a bit more convenient for comparing
many data sets. See the Calibration section for a recommended HDF5 file
viewer.
