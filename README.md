# GCMS AIA File Import and Non-negative Least squares

These programs will open a standard GCMS AIA data file and perform
non-negative least squares using a series of reference spectra. All of these
files should be contained in the same folder as the data. This folder needs to
be well structured, as described below.

## Reference MS Files

First of all, you are going to need a series of reference MS spectra to do the
fitting. I got my references from (massBank)[http://www.massbank.jp/?lang=en].
The format of these files is important, so a couple of examples are provided
in this repository (refcpd.txt and refcpd2.txt).

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

The first row in this file is critical. At the end, there are two values that
define the starting and stopping time points for integration. Change these
values based on the range that you've determined from the TIC of a calibration
run. The rest of the rows are for your data file information. The first column
will be the name of the calibration data file, and the second column needs to
be the concentration associated with that run. You don't have to add all of
the files here, but if they are not in this list, they won't be processed.
Alternatively, any line that starts with a '#' is a comment, and will be
ignored. In this way, you can comment out samples, and add some notes as to
why that sample was not used or whatever.

## Run Calibrations

Once you've updated the calibration information from above. You can run the
program 'calibration.py'. This runs through all of the reference spectra
defined in the 'reference\_files.txt' file. If a '.csv' file exists for a
particular reference file, then a calibration will be performed. 

All of the calibration data files will be processed and a calibration curve
generated. For each calibration sample, a plot of the reference-extracted data
will be generated in the calibration folder (refcpd\_fits.png). In addition, a
calibration curve plot is also generated (refcpd\_cal\_curve.png'), which
plots the integrated intensities and calibrated intensities vs the
concentrations. In addition, the calibration information is printed on the
graph for quick visual inspection. There is no need to write down this
calibration information.

Another file is also generated during this process: cal.h5. This is a HDF5
file that contains all of the calibration information for each standard. Do
not delete this file; it is essential for the next step. This is a very simple
file, and there are many tools for looking at the internals of an HDF5 file.
For example, (ViTables)[http://vitables.org/] is recommended.

## Process Sample Data

Run the program 'data.py' to process every AIA data file in the folder 'data'
using the calibration information that was determined from the steps above. 

This program opens the AIA file for the sample and performs non-negative least
squares analysis of the full data set using the reference spectra that are
listed in the 'reference\_files.txt' file. Using the calibration information
that was determined above, it finds the concentrations of those components in
the sample data. For every reference compound that has associated calibration
information, a plot is generated that overlays the TIC (gray) and extracted
reference fit (blue). The title of the plot provides the calibrated
concentration information. Visual inspection of these files is recommended. 

This file also generates another HDF5 file called 'data.h5'. This simple file
contains the concentration information for every component. This information
is identical to what is printed on the extraction plots above. However, this
is a bit more convenient for comparing many data sets. See the Calibration
section for a recommended HDF5 file viewer.
