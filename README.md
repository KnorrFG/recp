# recp

A command line tool to copy files by a regular expression.

Coppies all files that match a regular expression of a source path 
to a target path, which can be defined using the names of named capture 
groups from the source regex. Only Unix-paths are supported.

If the source regex describes a file, the target format string must to.
It is file to file or folder to folder. In the second case the target
folder must not exist (unless you used --skip-existing)

Since writing a regular expression is nearly always an iterative process
by default no coppying will be done, and only a preview will be displayed.
-n determines how many examples are shown. To copy the files use -c.

Every folder name and the file name are individually tested for being 
regulare expressions and a dot will be interpreted as normal dot, unless
any other sign of a regular expression is found, in which case the dot
will be interpreted as part of it.

It is possible to pass a mapping string with -s to map the value of a
capture group to something else. If a mapping string is given, also a 
mapping file must be given, which should be a pandas friendly csv (i.e. 
will be correctly loaded by pandas with default parameters)
If a mapping file and a mapping string are given the value of the mapped
variable will be replaced according to the table in the csv file

# Examples

``` bash 
recp "~/media/m/Rohdaten/nicepype/sesyn/033/nicepype/graff/033_1_setswitch(?P<run>\d)$/(?P<NIC_ID>\d+)/preprocessing/wr.*" "0/sub-{SubjectID}/ses-1/func/sub-{SubjectID}_ses-1_task-setswitch_run-{run}_bold.nii" -s "NIC_ID->SubjectID" -f "~/media/p/033/felix_2/shk_foo/set_switch_Runs_inclusion.csv" 
```

would produce:

``` bash
130 files found.
To copy the files use -c
/home/felix/media/m/Rohdaten/nicepype/sesyn/033/nicepype/graff/033_1_setswitch1/00115/preprocessing/wr20181129_064403boldAsetswitch1132ta16172020200033987033700000371s008a001.nii -> 0/sub-201/ses-1/func/sub-201_ses-1_task-setswitch_run-1_bold.nii
```

and the `set_switch_Runs_inclusion.csv` could look like this (changed for
privacy reasons):

```
NIC_ID,SubjectID
00115,201
00902,202
00823,203
```

# Installation

You can directly install via pip:
``` bash
pip install git+https://github.com/KnorrFG/recp.git
```
