.. _getting_started:

================================================================================
Getting Started
================================================================================


Pre requisites
================================================================================


Excel
````````````````````````````````````````````````````````````````````````````````
* Some version of Excel capable of saving an XLSX file recommended
* Open Office and Libre Office should also work but not exhaustively tested. 
* Recommended to start from the diagramming template provided within the
  package

python 2,7
````````````````````````````````````````````````````````````````````````````````
* Current implementation is in python 2.7 , This will be migrated to 3 sometime
  in the future.
* python requires the following packages 

  * xls2csv
  * openpyxl

.. code-block:: shell

    $ python -c 'import pkgutil; print(1 if pkgutil.find_loader("xls2csv") else 0)'
    1
    $ python -c 'import pkgutil; print(1 if pkgutil.find_loader("openpyxl") else 0)'
    1

Latex
````````````````````````````````````````````````````````````````````````````````
* TexLive or MikTex for latex. These are usually found bundled in linux
  distributions. MikTex can be installed on windows/Mac etc.

  * texlive/2016 is known good 

Get the scripts
````````````````````````````````````````````````````````````````````````````````

Clone from

.. code-block:: shell 

    $ git clone https://github.com/fractals-of-life/MakeWaves 


Snap shot of directory:

.. code-block:: shell

    |-- README.rst
    |-- doc
    |   |-- Makefile
    |   |-- README
    |   |-- build
    |   `-- source
    |       |-- _static
    |       |-- _templates
    |       |-- async.rst
    |       |-- conf.py
    |       |-- images
    |       |   |-- *.png
    |       |-- index.rst
    |       |-- intro.rst
    |       |-- step_by_step.rst
    |       `-- walkthrough.rst
    |-- py_scripts
    |   |-- draw_wave_tex.py
    |   `-- read_xlsx_val.py
    |-- run.sh
    |-- waveforms_template
    |   |-- job_list
    |   |-- async.aux
    |   |-- async.csv
    |   |-- async.log
    |   |-- async.pdf
    |   |-- async.png
    |   |-- async.svg
    |   |-- async.tex
    |   |-- template.aux
    |   |-- template.csv
    |   |-- template.log
    |   |-- template.pdf
    |   |-- template.png
    |   |-- template.svg
    |   |-- template.tex
    |   |-- waveforms__template.aux
    |   |-- waveforms__template.log
    |   |-- waveforms__template.pdf
    |   |-- waveforms__template.tex
    |   |-- waveforms__template.xlsx
    |   |-- waveforms_template.aux
    |   |-- waveforms_template.csv
    |   |-- waveforms_template.log
    |   |-- waveforms_template.pdf
    |   |-- waveforms_template.png
    |   |-- waveforms_template.svg
    |   `-- waveforms_template.tex

Versions
--------------------------------------------------------------------------------

v1.1:
    Changes to the intermediate CSV to use ';' instead of '.' as the delimiter.
    This has the knock on effect that the Annotation type can no longer have B|C:c:r
    This was anyway not used, so changed to B|C:r where B,C still works as chained i
    or baseline mode and  :r selects the annotation colour.
    :r is the default and cannot be over overridden, it is not Christmas yet!. 

Putting it to work
================================================================================

    *  Usage with the wrapper script
    *  Understanding Common Errors
    *  MISC set-up info that might be useful

The push-button wrappper script run.sh
--------------------------------------------------------------------------------

To use the push button wrapper script the following directory structure is
recommended::

  MakeWaves
  + README.rst
  + py_script
  + doc
  + dwsign_work_dir_1
  | + design1.xlsx
  + design_work_dir_2
  | + design2.xlsx
  ` run.sh

where run.sh is the push button script.
To use the script cd to the directory where the xlsx file is and use the
command as follows. All intermediate outputs and waveform will now be collected
in your design directory. 

tcsh command line:

.. code-block:: shell

  ../run.sh -wb *<workbook.xlsx>* [ -ws *<sheet_name>* | -all | -active ] -disp

    -wb : workbook file name with xlsx extension
    
    -ws : Name of the sheet within the worksheet
    -all: All available sheets within the specified workbook 
    -active : The active worksheet, which is the worksheet in focus when the
    file was saved.
    
    -disp : display the rendered output with xpdf

#. Generate a waveform description in the XL file by filling in clocks and
   signals.  The description is similar to a value change dump where only a
   change/transition needs to be recorded 

   Details of this can be found embedded in the example
   *waveform_template.xlsx* file. This file has 3 sheets, a file can have as
   many sheets as required.  Each sheet can be converted individually or all
   sheets can be converted in batch mode as described below.  Sheets can be
   exempt by adding the suffix '_nt' to its name.  If not, when the sheet is
   not empty a conversion will be attempted. Failing to comply with the
   template some random Tex error will be generated.  Please note tex errors
   are difficult to debug. 

   When converted in batch mode, by **-all** an option step will collate all the
   individual pages into one pdf file which is named <workbook_name>.pdf 
   
   The recommended approach to start a new waveform is by making a copy of the
   template sheet by right clicking on the tab and choosing copy.  Once the copy
   is made, and suitably renamed, the contents of the cells in the waveform area,
   NOTES. CLK_MARKS, ANNOTATE can all be cleared (select rows and delete).  The
   waveforms_template sheet can additionally be renamed with _nt suffix so that it
   is never converted but available as reference. This sheet is protected with no
   password.  The recommended methods for efficiently creating a waveform is
   detailed as cell comments. 

   Both Microsoft Excel and LibreOfficei can generate a compatible xlsx file.

#. Save this file. **Saving is important** as XL will generate values from formulas.
   Also the sheet that is in focus at the time of save will become the active
   sheet.

.. note::

  | **Q: Can the file be Directly saved to the H drive?**
  |    The file can be saved directly to the H drive, However, sometimes Excel
  |    would report the file to be read only and refuse to save.  In such instances,
  |    Save with a different name and save as with the old name rectifies the problem

#. For batch conversions of all sheets from a workbook use
  
.. code-block:: shell

  ../run.sh -wb waveforms_all.xlsx -all
 
To convert all sheets that are non empty. A sheet is empty if it has
no valid cell.  A sheet might unintentionally be classified as non empty, in
such case delete the sheet or add _nt' to the end of the sheet name. This can
be useful with sheets used to capture additional info. 

#. Rendering only the active sheets are useful in closing the description-render cycle

.. code-block:: shell

  ../run.sh -wb waveforms_all.xlsx -active -disp

or explicitly specifying the -ws sheet_name

.. code-block:: shell

  ../run.sh -wb waveforms_all.xlsx -ws <sheet_name> -disp

Use **-disp**, to open the rendered result. -disp can also be avoided, but a
previously opened pdf reloaded. However, if the pdf is open from windows,
tex will generate an ERROR. Please Refer ERROR section.


Common ERRORS:
================================================================================

#. Nature of Error when the CLK_MARKS section is enabled but no clock is defined
   i.e the clock column is '0' or empty. Ideally this should be the exact copy 
   of the clock for which the timing cycles are to be drawn, reference in the
   cell as =<cell_containing_the_name_of_the_clk>.

   In certain cases, although an end is specified excel wrongly calssifies
   cells beyond END as containing data. Simple resolution is to select i a few columns
   after END and delete them

.. code-block:: shell

    Traceback (most recent call last):
      File "./draw_wave_tex.py", line 565, in <module>
        tex_blk_drawedges = draw_edge_lines(signal_array, clock_edges,clk_filter, indent_level, marked_edges, tex_blk_drawedges)
      ...
      ...
    sre_constants.error: nothing to repeat
    ERROR: waveforms_template.tex convesion failed

#. Error when the pdf is open by another application, normally from windows.

.. code-block:: shell

    ERROR:!I can't write on file `waveforms_template.pdf'.
           (Press Enter to retry, or Control-D to exit; default file extension is `.pdf')
           Please type another file name for output
           ! Emergency stop.

#. Nature of the error when '...' get replaced with the Unicode equivalent. 

.. code-block:: shell

    Traceback (most recent call last):
      File "read_xlsx_val.py", line 68, in <module>
        result = convert_to_csv(ws_active)
      File "read_xlsx_val.py", line 24, in convert_to_csv
        csv_f.writerow([cell.value for cell in row])
    UnicodeEncodeError: 'ascii' codec can't encode character u'\u2026' in position 6: ordinal not in range(128)



MISC Notes
================================================================================


Getting hold of Required packages
--------------------------------------------------------------------------------
Script uses the following packages

* xls2csv 
* openpyxl

.. note::

    There is a specific version check for python, at the moment this is hardcoded
    to 2.7.10, you may override this in the script.

The following is needed for xlstocsv conversion from command line

.. code-block:: shell

    mkdir -p /home/username/local/lib/python2.6/site-packages/

The required packages for python may not be available on the host or a
managed system. Python allows mechanisms to install them locally. Creating
virtual env is another option.
With both pip available and access to the outside world, pip_install --user should
suffice for majority of the cases. This should default to ~/.local/ and
python would search this path by default.

.. code-block:: shell

    mkdir -p /home/username/local/lib/python2.6/site-packages/

    pip_install --user <package> 

A messy way is to use easy_install or using the set-up.py from a tarball. Both
these can lead to problems.

.. code-block:: shell

    echo $PYTHONPATH

    # append if not empty
    # Note: python version specific
    setenv PYTHONPATH /home/username/local/lib/<python_version>/site-packages
    # run once
    easy_install --prefix=$HOME/local xlsx2csv


Using the anaconda distribution
--------------------------------------------------------------------------------

Example commands

.. code-block:: shell

    module use /opt/ipython/modulefiles
    module load ipyhton 

    module load texlive/2016
    # sometimes it might complain about the tikz-timing library, just use what is
    # available, Seem to work

    python ./draw_wave_tex.py waveforms_cancel_sane.csv waveforms_cancel_sane.tex
    pdflatex waveforms_cancel_sane.tex
    pdflatex -interaction=nonstopmode waveforms_cancel_sane.tex

    inkscape -z -f waveforms_cancel_sane.pdf -l waveforms_cancel_sane.svg

    # Push button script
    ./run.sh -wb waveforms_all.xlsx -all -disp
    -disp : open xpdf after every render
    -all  : process all non empty sheets in xlsx, A sheet is considerd non empty if atleast one cell has a value.
            Check for validity of a sheet for parsing to produce waveforms is not considered.
    -active: render only the active sheet. Along with display can be used for development.
    <-ws sheet_name> : provide the explicit sheet name.
    
    svg: By default svg and png are generated. scg's are generally large files and hence the default dfeature will be turned off in the future.
   

.. figure:: ./images/xl1.png
   :scale: 50%
   :alt: An empty template

   The starting excel template.

   The cell boundaries allow easy segmentation of various areas. This empty
   template will not compile or generate a waveform.

