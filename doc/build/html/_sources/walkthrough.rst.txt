.. _walkthrough: 
================================================================================
Template and Markup
================================================================================

A worked out example with a recommended flow and other quirks

Organising the .xlsx file
================================================================================

An .xlsx file may contain more than one sheet. The sheets are to be uniquely named.

.. tip::
    **.xlsx** files is a zip archive which include xml descriptions for the various
    sheets and some other anciliary information. Although they can be placed under
    version control, zips are binary files and hence may not be the best
    way to feed git. An unzipped folder might be better suited for version
    control 

In addition, we encourage the user to add two sheets named index_nt and
Notes_nt. These will not be rendered but is a good mechanism to capture
information regarding the contents of the workbook as well as allow easy
navigation. Navigating between the sheets can be done with the sheets tab, but
maintaining this info within index and providing hyperlinks to sheets with a
short descriptive summary is highly recommended as a method of navigation.

.. figure:: ./images/settingup1.PNG
   :scale: 50%
   :alt: Setting up index 

   **Fig**:Recomended workbook layout 

   Tabs Index_nt, Notes_nt will not be rendered. Tab 'template' holds an empty
   wafeform template whole tab  'waveform_template' is a fully working example with
   hints added as cell comments.

Sheet naming convention
````````````````````````````````````````````````````````````````````````````````
* index_nt : for the cover sheet.
* notes_nt : For the end cover sheet, with any additional info 

.. note:: 

    the python parser script will look for the specific character seq **_nt**
    to ignore sheets that are not to be rendered.

* New sheets can be created by making a copy of template. However, ensure the
  sheet name is changed and the number removed.

* Keep names short, use the index instead to capture information regarding
  content.

* Sheet names may or may not be descriptive. For example when using the index
  as a navigation device it is perfectly acceptable to names the sheets as
  say set1, set2 etc.

.. note::

    Each sheet will be rendered to a pdf, svg or png file with its **sheet
    name**.  When used with **-all**, in addition to sheets being rendered
    individually they will also be bundeled into a single pdf with its name as
    the **workbook** name.

Working from the template
================================================================================

.. image:: ./images/template1.png
    :height: 640px
    :width: 640px
    :align: center 

Template is divided into 3 sections row wise.

    * Waveform description
    * Notes,
    * Annotations.

The other markers in the template are required by the python parser and is used as a mark-up
Mark-up usually follows the convention :*markup_name*: , i.e. a reserved mark-up_name bracketed by colons

.. note::
    Column 1 or A in the excel sheet cannot be empty. The parser interprets
    most markers when placed in the first column. The only exception is :END:

:SCALE: The number placed in the next column is used to control the scale of the waveform.
        Scale impact how many clocks are rendered and is an important parameter
        to fit the required number of clocks after allowing for margins on a ISO:A4
        paper in landscape mode.

        Default scale is 4, allowing unto 32 clocks (or xl columns) to be rendered 

:END:   When **:END:** is specified in any column within the same row as **:SCALE:**, the parser 
        limits time to that column. See Example TODO  

:TITLE: Text following title will be placed as the title of the waveform: See example TODO

:NOTE:  The notes area has three logical columns. The left most column just carries the text NOTE:
        This is provided so as to allow placement of multiline notes to form say a bulleted list.

.. table:: 

    ============ ============= ==================================================
    \:NOTE:      Marker        Text
    ============ ============= ==================================================
    NOTE:        cell_id>      Note accompanying the marker
    NOTE:        \             This is a continuation line of note above if 'Marker' is empty

    ============ ============= ==================================================

\

:CLK_MARKS: Control the edge and the clock on which the clock boundary is drawn.

            * D:|| is the marker for edge and 
            * p:1 identifies rising or posedge.\

\

.. table:: 

    ============ ============= ==================================================
    \:CLK_MARKS: Edge          Clock 
    ============ ============= ==================================================
    D:||         p:1           - name_of_the_clk_from_waveform_section 
                               - Do not type name, instead use reference
                               - type '=' in the cell
                               - click on the name of the clock in the waveform window 

    ============ ============= ==================================================

.. note::

   For edges to be drawn it is important that each column apart from any
   containing a break '|' should be numbered. 

:ANNOTATE: Mark-up to render edges, constraints etc. Mark-up and link_type
           together decide the intended style of annotation

           *Annotate* can specify two types of relations
               * E:<> specifies annotation drawn between edges
               * L:<> specifies annotation drawn between levels. These can be used to link sampling conditions or combinatorial results.
               * <> the exact type of edge and how they are interpreted varies. See table 
               Arcs/arrows are drawn with the form **<start_type>-<endtype>** where start and end are from the list below.
                  * >  arrow head
                  * \*  filled circle
                  * o  small caps 'o', open circle
                  * \|  dimension line

               Examples: o->, \*-\*, \*->, \|-\| 

           *Link_type* can take on two values to specify the type of link
               * C:r - Specifies a **C**\hained link. i.e a string of arcs connected back to back.
               * B:r - specified a **B**\aseline link. i.e the arcs all have the same start point, but multiple end points. 

           *Markers* column is composed of all remaining columns where each column links to a marker.
               * For a **chained (C:r)** link arcs are drawn between pairs of markers, left to right.
               * For **baseline (B:r)** links, arcs are drawn between the first specified mark and every successive edge. 
               * When *:ANNOTATE:*  is of type E:\|-\|, a constraint is drawn.
               This is different from the above modes in that it takes exactly two marks and
               the next column specifies a text to be placed following the annotation. As an
               example, consider annotating access time. Specify an edge of type E:\|-\|, C:r
               between two markers M1, M2 with text as 't_Acc'. See specific examples in table

.. note::

    When more than one constraint ends on the same destination, they are drawn
    one below other. However, this might cause them to overlap another waveform.
    When such conditions are detected the script emits an error of the form::
    **[WARNING      554]           add_arrows(): Multiple dimensions drawn may overlap a waveform, Add a spacer in excel if required R24> W24>**


.. |chained-arrows| image:: ./images/chained_arrows.png
    :scale: 50%

.. |baseline-arrows| image:: ./images/baseline_arrows.png
    :scale: 50%

.. |baseline-level| image:: ./images/baseline_level.png
    :scale: 50%

.. |constraint| image:: ./images/constraint.png
    :scale: 50%

.. |chained-sample| image:: ./images/chained_sampling.png
    :scale: 50%

.. |baseline-sample| image:: ./images/baseline_sampling.png
    :scale: 50%


.. table:: 

    ============ ============= ============================= ===================
    \:ANNOTATE:   Link Type     Markers/Action.               Render 
    ============ ============= ============================= ===================
    E:\o->        **C:r**      - C18> C19> C20>              |chained-arrows| 
                               - chained edge links 
    E:\o->        **B:r**      - C18> C19> C20>              |baseline-arrows| 
                               - baseline edge links
    **L:\*->**    **B:r**      - C18> C19> C20>              |baseline-level| 
                               - basline level links 
                               - useful for combinatorial
                                 dependencies, co-sampling
                                 etc 
    **L:\*-\***   **C:r**      - C18> C19>                   |chained-sample| 
                               - two co-samples signals 
    **L:\*-\***   **B:r**      - C18> C19>                   |baseline-sample| 
                               - two co-samples signals 
                               - **preferred method**
    E:\|-\|       **B:r**      - C18> C19> t_Acc             |constraint| 
                               - baseline edge links
    ============ ============= ============================= ===================


The empty template
================================================================================

.. |logo1| image:: ./images/template1.png
    :scale: 100%
    :height: 600px
    :width: 600px

.. |logo2| image:: ./images/template1_out.png
    :scale: 100%

.. table:: Source  -->  render 

   +---------------------------------------------------------------------------+
   |  source                                                                   |
   +---------------------------------------------------------------------------+
   |  |logo1|                                                                  |
   +---------------------------------------------------------------------------+
   |  Rendered ouptut                                                          |
   +---------------------------------------------------------------------------+
   |  |logo2|                                                                  |
   +---------------------------------------------------------------------------+


