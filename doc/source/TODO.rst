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
