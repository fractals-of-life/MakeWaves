MakeWaves
==========

# ------------------------------------------------------------------------------
# # CONTENTS
# ------------------------------------------------------------------------------
v1.1:
Changes to the intermediate CSV to use ';' instead of '.' as the delimiter.
this has the knock on effect that the Anotation type can no longer have B|C:c:r
This was anyway not used, so changed to B|C:r where B,C still works as chained i
or baseline mode and  :r selects the annotation colour.
:r is the defualt and cannot be over overidden yet, it is not christmas yet!. 
# ------------------------------------------------------------------------------
# CONTENTS
# ------------------------------------------------------------------------------
o Usage with the wrapper script
o Understanding Common Errors
o MISC setup info that might be useful

# ------------------------------------------------------------------------------
# Usage: With the push-button wrapper script run.sh
# ------------------------------------------------------------------------------
o Why use Excel or a similar utility?

    Using such an application provides a simple tabular interface which can often
  be intuitive for waveform entry. Further simple formulas and rudimentary
  intelligence provided by \*office can be used advantageously to generate a
  consistent maintainable and reproducible waveform. A drawing application can be
  used, but the main issue with those is maintainability, as well as effort
  required.  The current work flow is as follows and provides human readable text
  at all points. (the csv could help with some formatting)
    .xlsx -> .csv -> .tex
  The Excel step can be overstepped and a csv can be generated directly, for
  example by parsing a VCD. This can then be back annotated if required. At the
  moment there is no recommended flow for doing this but it should be possible
  from plain vcds.

o How to generate a waveform description in the XL file by filling in clocks and
  signals.
  The description is similar to a value change dump where only a
  change/transition needs to be recorded 

  Details of this can be found embedded in the example
  waveform_template.xlsx file.

  This file has 3 sheets, a file can have as many sheets as required.  Each sheet
  can be converted individually or all sheets can be converted in batch mode as
  described below.  Sheets can be exempt by adding the suffix '_nt' to its name.
  If not, when the sheet is not empty a conversion will be attempted. Failing to
  comply with the template some random Tex error will be generated.  Please note
  tex errors are extremely difficult to debug. 

  When converted in batch mode, by -all an option step will collate all the
  individual pages into one pdf file which is named <workbook_name>,pdf 
 
  The recommended approach to start a new waveform is by making a copy of the
  template sheet by right clocking on the tab and choosing copy.  Once the copy
  is made, and suitably renamed, the contents of the cells in the waveform area,
  NOTES. CLK_MARKS, ANNOTATE can all be cleared (select rows and delete).  The
  waveforms_template sheet can additionally be renamed with _nt suffix so that it
  is never converted but available as reference. This sheet is protected with no
  password.  The recommended methods for efficiently creating a waveform is
  detailed as cell comments. 
  
  Seems to work with both Microsoft Excel and LibreOffice.

o Save this file. Saving is important as XL will generate values from formulas.
  Also the sheet that is in focus at the time of save will become the active
  sheet.

  Q: Can the file be Directly saved to the H drive?
  The file can be saved directly to the H drive, However, sometimes Excel
  would report the file to be read only and refuse to save.  In such instances,
  Save with a different name and save as with the old name rectifies the problem

o Active sheets are useful in closing the description-render cycle.

  ./run.sh -wb waveforms_all.xlsx -active -disp

or explicitly specifying the -ws sheet_name

  ./run.sh -wb waveforms_all.xlsx -ws <sheet_name> -disp

  Use -disp, to open the rendered result. -disp can also be avoided, but a
previously opened pdf reloaded. However, if the pdf is open from windows,
tex will generate an ERROR. Please Refer ERROR section.

o For batch conversions of all sheets from a workbook use
  
  ./run.sh -wb waveforms_all.xlsx -all
 
  This will convert all sheets that are non empty. A sheet is empty if it has
no valid cell.  A sheet might unintentionally be classified as non empty, in
such case delete the sheet or add _nt' to the end of the sheet name. This can
be useful with sheets used to capture additional info. 

.. caution::

    # Common ERRORS:
    # ------------------------------------------------------------------------------

    1) Nature of Error when the CLK_MARKS section is enabled but no clock is defined
       i.e the clock column is '0' or empty. Ideally this should be the exact copy 
       of the clock for which the timing cycles are to be drawn, reference in the
       cell as =<cell_containitng_the_name_of_the_clk>.
    
        Traceback (most recent call last):
          File "./draw_wave_tex.py", line 565, in <module>
            tex_blk_drawedges = draw_edge_lines(signal_array, clock_edges,clk_filter, indent_level, marked_edges, tex_blk_drawedges)
          ...
          ...
        sre_constants.error: nothing to repeat
        ERROR: waveforms_template.tex convesion failed
        
    2) Error when the pdf is open by another application, normally from windows.
    
        ERROR:!I can't write on file `waveforms_template.pdf'.
               (Press Enter to retry, or Control-D to exit; default file extension is `.pdf')
               Please type another file name for output
               ! Emergency stop.
    
    3) Nature of the error when '...' get replaced with the unicode equivalent. 
        Traceback (most recent call last):
          File "read_xlsx_val.py", line 68, in <module>
            result = convert_to_csv(ws_active)
          File "read_xlsx_val.py", line 24, in convert_to_csv
            csv_f.writerow([cell.value for cell in row])
        UnicodeEncodeError: 'ascii' codec can't encode character u'\u2026' in position 6: ordinal not in range(128)



 MISC Notes
 ------------------------------------------------------------------------------


 ------------------------------------------------------------------------------
 Getting hold of Required packages
 ------------------------------------------------------------------------------
 Script uses the following packages
 xls2csv, openpyxl
 
 There is a specific version check for python, at the moment this is hardcoded
 to 2.7.10, you may override this in the script.

 The following is needed for xlstocsv converion from command line

.. code::

    mkdir -p /home/user/local/lib/python2.6/site-packages/

 The required packages for python may not be available on the host or a
 managed system. Python allows mechanisms to install them locally. Creating
 vritiual env is another option.
 with both pip available and access to the outside world, pip_install --user should
 suffice for majority of the cases. This should default to ~/.local/ and
 python would search this path by default.

.. code::

    pip_install --user <package> 

 A messy way is to use easy_install or using the setup.py from a tarball. Both
 these can lead to problems.

 .. code::

    echo $PYTHONPATH

    # append if not empty
    # Note: python version specific

    setenv PYTHONPATH /home/<user>/local/lib/<python_version>/site-packages

    # run once

    easy_install --prefix=$HOME/local xlsx2csv

------------------------------------------------------------------------------
Using the anaconda distribution
------------------------------------------------------------------------------
.. code::

    module use /opt/ipython/modulefiles
    module load ipyhton 

    module load texlive/2016

    # sometimes it might complain about the tikz-timing library, just use what is
    # available, Seem to work

    python ./draw_wave_tex.py waveforms_cancel_sane.csv waveforms_cancel_sane.tex
    pdflatex waveforms_cancel_sane.tex
    pdflatex -interaction=nonstopmode waveforms_cancel_sane.tex

    inkscape -z -f waveforms_cancel_sane.pdf -l waveforms_cancel_sane.svg

Push button script
------------------------------------------------------------------------------
cd <project_dir_containing_xlsx>

../run.sh -wb waveforms_all.xlsx -all -disp

-disp : open xpdf after every render
-all  : process all non empty sheets in xlsx, A sheet is considerd non empty if atleast one cell has a value.
        Check for validity of a sheet for parsing to produce waveforms is not considered.
-active: render only the active sheet. Along with display can be used for development.
<-ws sheet_name> : provide the explicit sheet name.

svg: By default svg and png are generated. scg's are generally large files and hence the default dfeature will be turned off in the future.

