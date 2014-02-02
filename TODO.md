Add reference files without having the folder be processed.
    -- This can be done by not including a CSV file. That was my problem.

Remove reference builder from the AIAFile class, make this its own separate
function. When automating make one copy of the referece array that gets passed
into each chromatogram being processed.

Add background command line arguments into data script as well. This will be
essentially the same code as used for the calibration script.
