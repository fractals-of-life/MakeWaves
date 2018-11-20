.. _TODO:

================================================================================
Things to do 
================================================================================


#. **When drawing a clock edge, allow a choice for line style.**

    Rational: When rendering timing diagrams with asynchronous clocks clock
    edges from two unrealted clocks improve legibility 

#. **Derived clock with 50% duty cycle**
    Rational: when negedge has no timing significance, 50% duty cycle may not serve much
    pourpose in a timing diragram. However, DDR representation or other mixed
    signal interfaces, for example will be more meaningful with a 50% clock.

#. **Enforce automatic ordering of notes**
    Rational: A good arrangement should allow easy location of a note within the
    waveform. Notes a re deliberately marked with a grey scale callout to avoid
    clutter, Ordering notes left to rt, top to bottom ie a raster scan order might
    make it easied to locate in the diagram. This mechanism needs to be automated,
    ie the Notes on the sourece can be in any order but when rendered they should
    follow raster ordering.

#. **Method to mark a region**
    Rational: To highlight a certain section of the waveform, one could draw
    bounding boxes aronnd certain signals/time. Bounding boxes can be de dawn with
    a tex command such as below and use a pin to identify the region. A mechanisms
    shoulw be allowed to then reference this pin in the NOTES section to add
    comments to it., 

    .. code-block:: tex
    
       \draw [rounded corners, orange, thin]
         ($(A.mid)+(-0.5,1)$) 
         rectangle 
         ($(Can.mid)-(-0.5,1)$)
         node [pos=0,circle,draw,pin=region\_label] {};

#. **Method to mark a region**
