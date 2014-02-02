Add reference files without having the folder be processed.
    -- This can be done by not including a CSV file. That was my problem.

Add comment lines to reference ms files.

Remove reference builder from the AIAFile class, make this its own separate
function. When automating make one copy of the referece array that gets passed
into each chromatogram being processed.
