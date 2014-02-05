Add reference files without having the folder be processed.
    -- This can be done by not including a CSV file. That was my problem.

Remove reference builder from the AIAFile class, make this its own separate
function. When automating make one copy of the referece array that gets passed
into each chromatogram being processed.

I made bkg_time argument a string for comparisons. I didn't want to end up
with floating point problems. This may cause problems if you use two string
reps of the same number '0.12' vs '0.120', for example.


