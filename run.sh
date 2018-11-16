#!/bin/tcsh
set WAVEMAKER_WORK = $cwd:t
set WAVEMAKER_BASE = $cwd:h
echo $WAVEMAKER_WORK
echo $WAVEMAKER_BASE


cat<<EOF
-- -----------------------------------------------------------------------------
o  Requires python 2.7.10 for xls to csv, csv to tex conversion
   +  Requires modules sys, re, openpyxl, csv 
o  Requires pdflatex version 2016 or later for tex to pdf conversion
   +  Requires package {tikz-timing}[2011/01/09] or higher with advancednodes and 
   +  package meta.arrows.
o  Requires Inkscape for pdf to svg/png conversion
o  Requires xpdf for auto viewer
-- -----------------------------------------------------------------------------
EOF

set test = 0

#module load python/2.7.10_rhe5_64

module load texlive/2016
@ test = $test + $? 
echo $test

echo "-- -----------------------------------------------------------------------------"
python --version
@ test = $test + $? 
echo $SHELL
@ test = $test + $? 
echo "checking pdflatex ..."
which pdflatex
@ test = $test + $? 
pdflatex --version
@ test = $test + $? 
echo "checking inkscape ..."
which inkscape
@ test = $test + $? 
inkscape --version
@ test = $test + $? 
echo "checking xpdf ..."
which xpdf
@ test = $test + $? 
echo $test
xpdf -v
echo "-- -----------------------------------------------------------------------------"

if ( $test ) then
    echo "ERROR: Required tools not found, see above."
    exit 1
endif


if ( $# == 0 ) then
    echo "ERROR Empty arcgument list..."
    echo "Usage -wb <workbook_name.xlsx> [-wc <worksheet> | -all | null=active_sheet] [-disp]"
    exit 1
endif

set display_on = 0
set lst = ( $* )

while ($#)
    if ( "$1" == "-wb" ) then
        shift
        set xls_file = $WAVEMAKER_BASE/$WAVEMAKER_WORK/$1
  
        if ( $xls_file:e !~ "xlsx" ) then
  
            echo "ERROR: Unsupported file format $xls_file, expected xlsx"
            exit 1
  
        endif
  
    else if ( "$1" == "-ws" ) then
  
        shift
        set xls_sheet = $1
  
    else if ( "$1" == "-all" ) then
  
        echo "INFO : Sheet names will be collected to job_list"
        set xls_sheet = "-all"
  
    else if ( "$1" == "-active" ) then
  
        echo "INFO : Only render active sheet"
        set xls_sheet = "-active"
  
    else if ( "$1" == "-disp" ) then
   
       set display_on = 1 
  
  
    else
        echo "ERROR incomplete or unsupported argument list..."
        echo "Usage -wb <workbook_name.xlsx> [-wc <worksheet> | -all | null=active_sheet] [-disp]"
        exit 1
    endif
    shift 
end

if (! $?xls_sheet) then
    set xls_sheet = "-active"
endif

echo "Working on ... Wokbook $xls_file, sheets $xls_sheet"


#[ -z "$1" ] && echo "use: $0 <waveform_name>" && exit 1
#WAVEFORM=$1
#shift

# -------------------------------------------------------------------------------
# Generate csv from xlsx output is worksheet .csv
# -------------------------------------------------------------------------------
python ../py_scripts/read_xlsx_val.py $xls_file $xls_sheet

echo `cat job_list`
foreach WAVEFORM (`cat ./job_list`)
    echo $WAVEFORM
  
    # -------------------------------------------------------------------------------
    # Check csv and produce tex
    # -------------------------------------------------------------------------------
    [ ! -f ${WAVEFORM}.csv ] && echo "File not found: ${WAVEFORM}.csv" && exit 1
  
    echo "INFO : Generating tex file ..."
    python ../py_scripts/draw_wave_tex.py ${WAVEFORM}.csv ${WAVEFORM}.tex 4 
    
    if ( $? == 0 ) then
          echo "csv to tex...OK"
        else
          echo "ERROR: ${WAVEFORM}.tex convesion failed"
          exit;
    endif 
    
    # -------------------------------------------------------------------------------
    # Check tex and produce pdf 
    # -------------------------------------------------------------------------------
    [ ! -f ${WAVEFORM}.tex ] && echo "File not found: ${WAVEFORM}.tex" && exit 1
    echo "Invoking TeX for pdf ..."
    #pdflatex -interaction=nonstopmode ${WAVEFORM}.tex
    pdflatex -interaction=batchmode ${WAVEFORM}.tex
    set latex_suceess = $?
  
    set all_errors =  `grep -c ! -A4 ${WAVEFORM}.log`
    set filtered_error = `grep ! -A4 ${WAVEFORM}.log | egrep -c 'pgf@anchor'`
    echo "Parsing Log file, all_errors = $all_errors filtered_Error =  $filtered_error" 
    if ( latex_success == 0  || ( $all_errors == 1 && $filtered_error == 1 )) then
          echo "tex to pdf...OK"
        else
          echo "ERROR: ${WAVEFORM}.pdf convesion failed, see log file line starting with !"
          grep ! -A4 ${WAVEFORM}.log
          exit;
    endif 
    
    # -------------------------------------------------------------------------------
    # Check pdf and produce svg 
    # -------------------------------------------------------------------------------
    [ ! -f ${WAVEFORM}.pdf ] && echo "File not found: ${WAVEFORM}.pdf" && exit 1
    echo "Invoking inkscape for pdf to svg..."
    inkscape -z -f ${WAVEFORM}.pdf -l ${WAVEFORM}.svg
    
    if ( $? == 0 ) then
          echo "pdf to svg...OK"
        else
          echo "ERROR: ${WAVEFORM}.svg convesion failed"
          exit;
    endif 
    
    # -------------------------------------------------------------------------------
    # Check pdf and produce png. Can be opened in firefox and refreshed on run 
    # -------------------------------------------------------------------------------
    convert -density 300 ${WAVEFORM}.pdf -quality 120 ${WAVEFORM}.png
    
    if ( $? == 0 ) then
          echo "pdf to png...OK"
        else
          echo "ERROR: ${WAVEFORM}.png convesion failed"
          exit;
    endif 
  
    if ($display_on) then
      xpdf -z width -g 1900x1200  ${WAVEFORM}.pdf &
    endif

end

# -------------------------------------------------------------------------------
# collate all sheets from the workbook into a single pdf 
# -------------------------------------------------------------------------------
if ($xls_sheet == "-all") then
  set xls_f_name = $xls_file:t:r
  
cat > $xls_f_name.tex << EOF
\documentclass[landscape]{report} 
\usepackage{pdfpages}
\begin{document}
EOF
  
  foreach WAVEFORM (`cat ./job_list`)
    echo "\\includepdf[pages=-]{${WAVEFORM}.pdf}" >> $xls_f_name.tex 
  end
  echo "\\end{document}" >> $xls_f_name.tex


  [ ! -f ${xls_f_name}.tex ] && echo "File not found: ${xls_f_name}.tex" && exit 1
  echo "Invoking TeX for collating worksheets into a single pdf ..."
  #pdflatex -interaction=nonstopmode ${xls_f_name}.tex
  pdflatex -interaction=batchmode ${xls_f_name}.tex
  
  
  if ( $? == 0 ) then
        echo "tex to pdf...OK"
      else
        echo "ERROR: ${xls_f_name}.pdf convesion failed"
        #exit;
  endif 

endif

