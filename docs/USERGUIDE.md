# Basics of working with GCMS data files

## Export the data

First of all, be sure to export your GCMS data in a common data format, such
as [AIA, ANDI, or
CDF.](http://en.wikipedia.org/wiki/Mass_spectrometry_data_format#ANDI-MS_or_netCDF)
It turns out that all of these formats [are
related](https://www.unidata.ucar.edu/support/help/MailArchives/netcdf/msg05748.html)
in that they are all based off of [Network Common Data Format
(netCDF)](http://en.wikipedia.org/wiki/NetCDF), so they may have the file
extension "AIA" or "CDF". This file type may not be the default for your
instrument, so consult the documentation for your GCMS software to determine
how to export your data in these formats. 

## Set up the processing environment

In order to process these files, run IPython from a terminal (command prompt
in Windows) in the folder containing the "gcms.py" file (which is the base
folder for this repository).  There are a (at least) two ways to do this that
involve the command `cd` (change directory), which can be run from the
terminal or an IPython session. For example (`$` is the command prompt, `In:`
is the IPython prompt):

    home>$ ipython
    In: %cd "path-to-gcms-folder"
    Out: path-to-gcms-folder
    In:

or:

    home>$ cd path-to-gcms-folder
    gcms>$ ipython
    In:

The "path-to-gcms-folder" is a valid path to the folder with "gcms.py". It can
take a little practice, but this gets easier very quickly. I'll assume you use
the second form of this as it makes using the [IPython
notebook](http://ipython.org/notebook.html) much easier later.

## Read data file

First of all, you will need to `import` the "gcms.py" file to make the code
accessible to the IPython environment. This file contains a class called
`AIAFile` that reads and processes the GCMS files. AIAFile takes one argument,
which is a string with the file name. This string must have the path
information if the file is not in the same directory as "gcms.py".
Sample data files are contained in a folder called "data". 

    In: import gcms
    In: data = gcms.AIAFile('data/datasample1.CDF')

The variable `data` now contains our processed GCMS data set. You can see its
contents using tab completion in IPython (`<tab>` refers to the tab key).

    In: data.<tab>
    data.filename data.intensity data.nnls data.ref_build data.times
    data.integrate data.masses data.tic

All of these attributes are either data that describe or functions that modify
(methods) our dataset. You can inspect these attributes very easily in
IPython by just typing the name at the prompt.

    In: data.times
    Out: 
    array([0.08786667, ..., 49.8351])
    In: data.tic
    Out:
    array([158521., ..., 0.])

This is a short description of these initial attributes:

* *filename*: This is the name of the file that you imported.

* *times*: A Numpy array of the times that each MS was collected.

* *tic*: A Numpy array of the total ion chromatogram intensities.

* *masses*: A Numpy array the masses that cover the data collected by the MS.

* *intensity*: This is the 2D Numpy array of raw MS intensity data. The columns
correspond to the masses in the `masses` array and the rows correspond to the
times in the `times` array. 

The remaining attributes `ref_build`, `nnls`, and `integrate` are functions
that deal with the non-negative fitting routine and are covered in later
sections. 

## Simple plotting

We can easily plot these data using the plotting package Matplotlib. As an
example, let's try making a plot of our total ion chromatogram. In this case,
`data.times` will be our "x-axis" data, and `data.tic` will be our "y-axis"
data.

    In: import matplotlib.pyplot as plt
    In: plt.plot(data.times, data.tic)
    Out:
    [<matplotlib.lines.Line2D at 0x7f34>]
    In: plt.show()

This should produce a pop-up window with an interactive plot of your TIC.
(This should be fairly quick. However, sometimes the plot initially appears
behind the other windows, so be sure to scroll through your windows to find
it.)

![Total ion chromatogram](./images/tic.png)

One drawback here is that you have to type these commands every time you want
to see this plot. Of course, you can simply put all of these commands into a
text file and run it with Python directly. Copy the following code into a file
called "tic_plot.py". 

    import matplotlib.pyplot as plt
    import gcms

    data = gcms.AIAFile('data/datasample1.CDF')
    plt.plot(data.times, data.tic)
    plt.show()

One difference here is that it is common to do all imports at the top of the
file, so you know where external code is being brought into play. Run this
using the `python` command from the terminal.

    gcms>$ python tic_plot.py

The window with your plot will appear now; you will not be able to work in the
terminal until you close this window. Alternatively, you can run this program
directly from IPython.

    gcms>$ ipython
    In: %run tic_plot.py

This also pops open a new window with the plot. It has the advantage, however,
that once the window is closed, you are dropped back into an IPython session
that "remembers" all of the variables and imports that you created in your
program file. In our example above, once the plot window is closed, your
IPython session will have `gcms`, `plt`, and `data` (our GCMS AIA file)
available.  This is very useful if you want to continue to work interactively
with your data, and it is a great way to remove a bunch of repetitive typing.

## Working with multiple data sets

In our example above, we opened our dataset into a variable called `data` in
order to be able to plot the TIC. If you want to manipulate more than one data
set, the procedure is exactly the same, except that you will need to use
different variable names for your other data sets. 

    In: data2 = gcms.AIAFile('data/datasample2.CDF')

These two data sets can be plot together on the same figure by doing the
following:

    In: plt.plot(data.times, data.tic)
    Out:
    [<matplotlib.lines.Line2D at 0x7f34>]
    In: plt.plot(data2.times, data2.tic)
    Out:
    [<matplotlib.lines.Line2D at 0x02e3>]
    In: plt.show()

The following window should appear on the screen. (There is a blue and green
line here that are a little hard to see in this picture. Zoom in on the plot
to see the differences.)

![Two tic plotted together](./images/tic2.png)


# Reference MS Files

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

# Calibration Data

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

# Run Calibrations

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

# Process Sample Data

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
